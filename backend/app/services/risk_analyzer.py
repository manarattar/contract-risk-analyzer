import json
import re
import time
from typing import List, Dict

import openai
from openai import OpenAI

from app.config import get_settings
from app.schemas import (
    ClauseAnalysis, ClauseCategory, AffectedParty,
    ContractAnalysis, ContractQualitySummary,
    ContradictionFinding, MissingClause, MissingClauseRelevance, RiskLevel,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMPORTANT_CLAUSE_TYPES = [
    "Termination", "Liability", "Payment", "Confidentiality",
    "Intellectual Property", "Data Protection", "Governing Law",
    "Non-compete", "Renewal", "Indemnity", "Dispute Resolution",
]

CATEGORY_TO_RISK_LEVEL: Dict[str, RiskLevel] = {
    "Best Practice":        RiskLevel.LOW,
    "Acceptable Standard":  RiskLevel.LOW,
    "Minor Improvement":    RiskLevel.LOW,
    "Moderate Risk":        RiskLevel.MEDIUM,
    "High Risk":            RiskLevel.HIGH,
    "Critical Risk":        RiskLevel.HIGH,
}

# Soft score bounds per category — used to clamp the LLM score into a sensible range
CATEGORY_SCORE_BOUNDS: Dict[str, tuple] = {
    "Best Practice":        (0,  20),
    "Acceptable Standard":  (10, 40),
    "Minor Improvement":    (21, 40),
    "Moderate Risk":        (41, 60),
    "High Risk":            (61, 80),
    "Critical Risk":        (81, 100),
}

# ---------------------------------------------------------------------------
# System prompt — applies to every LLM call
# ---------------------------------------------------------------------------

SYSTEM_MESSAGE = (
    "You are a senior commercial contract analyst with 20 years of experience. "
    "You are calibrated and realistic: you recognize that most professional contracts "
    "contain standard clauses that are commercially normal and should not be flagged as risks. "
    "You distinguish clearly between real legal danger, ordinary contract structure, and minor "
    "drafting improvements. When in doubt about whether something is a risk or normal practice, "
    "lean toward recognising it as normal. "
    "Always return valid JSON only — no explanations, no markdown, no preamble."
)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

DETECT_PROMPT = """Analyze this contract excerpt and return ONLY valid JSON.

{text}

{{
  "contract_type": "one of: Service Agreement|Employment|NDA|Lease|Software License|Consulting|Software Development|Partnership|Sales|Other",
  "subject_matter": "1 sentence — what this contract is actually about",
  "apparent_weaker_party": "Client|Vendor|Employee|Tenant|Both Equal|Unknown",
  "jurisdiction_hint": "any jurisdiction or governing law clues, or Unknown",
  "red_flags_preview": ["up to 3 immediately obvious issues — leave empty if none"]
}}"""


CLAUSE_PROMPT = """Analyze this contract clause against standard commercial contracting practice.

Contract context: {contract_type} | Apparently weaker party: {weaker_party}
Previous clause: {prev_summary}

━━━ STANDARD CLAUSE BASELINES — Do NOT score these as Moderate Risk or higher ━━━
• Liability cap = contract value with carve-outs for gross negligence / fraud / data breach
  → Acceptable Standard, score 15–25
• Milestone-based payment in software / service agreements
  → Acceptable Standard, score 10–20
• Written change request / change order process
  → Best Practice, score 5–15
• 30-day payment terms
  → Acceptable Standard, score 10–20
• 30-day or longer termination notice
  → Acceptable Standard, score 10–25
• Arbitration or mediation with named venue and rules
  → Acceptable Standard, score 10–20
• Entire agreement clause requiring written amendments
  → Acceptable Standard, score 10–15
• IP: client owns custom deliverables; provider retains pre-existing IP with license to client
  → Best Practice, score 5–15
• Confidentiality with exceptions for legal obligations, court orders, regulatory requirements
  → Acceptable Standard, score 10–20
• Governing law naming a clear, specific jurisdiction
  → Acceptable Standard, score 5–15

━━━ SCORING RUBRIC ━━━
• 0–20: Best Practice — clear, balanced, commercially normal
• 21–40: Acceptable Standard / Minor Improvement — legally reasonable, small refinements possible
• 41–60: Moderate Risk — material ambiguity, imbalance, or missing detail that could cause disputes
• 61–80: High Risk — significant exposure, unfairness, or uncertainty
• 81–100: Critical Risk — self-defeating, likely unenforceable, removes essential protections

━━━ FALSE POSITIVE GUARDRAIL ━━━
Before assigning Moderate Risk or higher, confirm:
1. Is this actually harmful, or just a normal contractual mechanism?
2. Would a competent commercial lawyer normally accept this clause?
3. Is there a real legal/commercial risk, or just room for improvement?
If the answers suggest normal practice, assign Acceptable Standard or Minor Improvement.

━━━ CATEGORIES ━━━
Best Practice — clear, balanced, commercially standard
Acceptable Standard — legally reasonable, minor refinements possible
Minor Improvement — mostly fine, could benefit from more specificity
Moderate Risk — ambiguity or imbalance that could realistically cause disputes
High Risk — significant exposure, contradiction, or unfairness
Critical Risk — self-defeating, likely unenforceable, or removes essential protections

Clause to analyze:
{text}

Return ONLY this JSON (no other text):
{{
  "clause_title": "short descriptive title (max 8 words)",
  "clause_type": "Termination|Liability|Payment|Confidentiality|Intellectual Property|Data Protection|Governing Law|Non-compete|Renewal|Indemnity|Dispute Resolution|Other",
  "category": "Best Practice|Acceptable Standard|Minor Improvement|Moderate Risk|High Risk|Critical Risk",
  "risk_score": <integer 0-100 per rubric — must be consistent with category>,
  "affected_party": "Client|Provider|Both Parties",
  "what_works_well": "what the clause does well in 1 sentence, or 'None' if Critical Risk",
  "risk_explanation": "the actual issue if category is Moderate Risk or higher; otherwise 'None' or a brief minor note",
  "suggested_revision": "suggested improvement in 1–2 sentences, or 'None required' if Best Practice or Acceptable Standard",
  "negotiation_advice": "negotiation guidance in 1 sentence, or 'None required' if Best Practice",
  "enforceability_concern": <true only if this clause would likely be unenforceable in most jurisdictions, false otherwise>
}}"""


SUMMARY_PROMPT = """Based on these analyzed contract clauses, provide a calibrated overall assessment.

Contract type: {contract_type}

Clauses analyzed:
{clause_summary}

Missing clause types (from standard list): {missing_types}
Clause types found: {found_types}

━━━ SCORING CALIBRATION ━━━
• 0–20: Excellent — all or nearly all clauses Best Practice
• 21–35: Well-drafted — mostly Best Practice / Acceptable Standard, only minor improvements
• 36–55: Reasonable — some meaningful issues but no critical defects
• 56–75: Needs revision — several significant problems
• 76–100: Severely defective — critical risks or predatory clauses present

IMPORTANT:
• A contract where most clauses are Best Practice or Acceptable Standard MUST score 20–35
• Do NOT score above 65 unless there are multiple High Risk or Critical Risk clauses
• If the contract is good, say so explicitly in document_summary

━━━ MISSING CLAUSE RELEVANCE FOR {contract_type} ━━━
Classify each missing clause as Essential / Recommended / Optional:
• Non-compete: usually Optional / Not Required in service / software development agreements
• Renewal: Optional / Not Required if agreement is project-based with fixed scope
• Acceptance Criteria: Recommended to Essential for software development contracts
• Data Protection: Essential if personal data is processed; Recommended otherwise
• Force Majeure: Recommended but not Essential
• Indemnity: Recommended — moderate issue if absent in commercial agreements
• Security Requirements: Recommended to Essential for software handling user data

━━━ OUTPUT FORMAT ━━━
Return ONLY this JSON:
{{
  "document_summary": "one realistic paragraph — explicitly state if the contract is well-drafted; do not force risk framing on good contracts",
  "analysis_perspective": "Balanced / both parties",
  "overall_risk_score": <integer 0-100 per calibration above>,
  "overall_risk_level": "Low|Medium|High",
  "quality_summary": {{
    "overall_legal_structure": "Weak|Adequate|Strong",
    "commercial_balance": "One-sided|Mostly Balanced|Balanced",
    "drafting_clarity": "Poor|Adequate|Strong",
    "enforceability_confidence": "Low|Medium|High",
    "negotiation_readiness": "Not ready|Needs revision|Ready with minor refinements"
  }},
  "final_recommendation": "Unsafe to sign|Needs significant revision|Reasonable with revisions|Ready with minor refinements",
  "main_risks": ["only genuine High Risk or Critical Risk findings — not standard clauses"],
  "minor_improvements": ["Minor Improvement and Acceptable Standard refinement suggestions"],
  "best_practice_clauses": ["clause titles that are Best Practice or Acceptable Standard"],
  "missing_clauses": [
    {{"clause_type": "...", "relevance": "Essential|Recommended|Optional / Not Required", "reason": "1 sentence why"}}
  ]
}}"""


CONTRADICTION_PROMPT = """Perform a deep logical analysis of this contract. Look ONLY for genuine logical contradictions between clauses.

Contract clauses:
{clauses_text}

━━━ VALID CONTRADICTIONS — only flag these types ━━━
• One clause grants client EXCLUSIVE ownership of deliverables; another grants provider EXCLUSIVE ownership of the same work
• A confidentiality clause requires protection; another clause explicitly permits UNRESTRICTED disclosure of the same information
• A warranty GUARANTEES a specific performance outcome; a liability clause FULLY disclaims all responsibility for that same performance
• A fixed-price payment clause; a separate clause allows UNILATERAL price increases without client approval
• A clause says Agreement requires WRITTEN amendments only; another clause says oral agreements are binding

━━━ INVALID — Do NOT flag these ━━━
• IP ownership ≠ change approval procedures (different subjects, not conflicting)
• Milestone payment ≠ termination payment for accepted work (compatible timing)
• Liability cap carve-outs ≠ making the cap self-defeating (carve-outs are standard and expected)
• Data protection obligations ≠ confidentiality (complementary, not conflicting)
• Change request procedures ≠ scope definitions (compatible processes)
• A party having more rights than the other ≠ a contradiction (may be imbalance, but not a logical conflict)

━━━ VALIDATION REQUIREMENT ━━━
For each potential contradiction, complete this proof:
  Clause A says: [exact claim]
  Clause B says: [exact conflicting claim]
  These cannot both be true because: [specific logical reason]

If you cannot complete the proof, do NOT include it.
Return [] if no genuine contradictions exist.

Return ONLY a JSON array:
[
  {{
    "clause_a_title": "first clause title",
    "clause_b_title": "second clause title, or null if self-defeating",
    "contradiction_type": "Logical Conflict|Self-Defeating|Ownership Conflict|Nullification|Scope Conflict",
    "severity": "Low|Medium|High",
    "description": "Clause A says [X]. Clause B says [Y]. These conflict because [Z].",
    "impact": "practical consequence in 1 sentence"
  }}
]"""


QA_PROMPT = """Answer the following question about this contract based only on the provided contract sections.
Do not provide legal advice. If the answer is not in the provided text, say so clearly.

Contract sections:
{context}

Question: {question}

Answer in plain English, 2-4 sentences."""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(content: str):
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s*```\s*$", "", content, flags=re.MULTILINE)
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
        if match:
            return json.loads(match.group(1))
        raise


def _get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def _call_llm(client: OpenAI, settings, prompt: str, temperature: float = 0.2) -> str:
    # Retry up to 3 times on rate-limit (429) with 65-second backoff
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            if attempt < 2:
                time.sleep(65)  # Gemini free tier resets each minute
            else:
                raise


def _category_to_risk_level(category: str) -> RiskLevel:
    return CATEGORY_TO_RISK_LEVEL.get(category, RiskLevel.MEDIUM)


def _clamp_score_to_category(score: int, category: str) -> int:
    lo, hi = CATEGORY_SCORE_BOUNDS.get(category, (0, 100))
    return max(lo, min(hi, score))

# ---------------------------------------------------------------------------
# Stage 1 — Contract context detection
# ---------------------------------------------------------------------------

def _detect_context(full_text: str) -> dict:
    settings = get_settings()
    client = _get_client()
    try:
        content = _call_llm(client, settings, DETECT_PROMPT.format(text=full_text[:3000]))
        return _extract_json(content)
    except Exception:
        return {
            "contract_type": "Unknown",
            "subject_matter": "Unknown",
            "apparent_weaker_party": "Unknown",
            "jurisdiction_hint": "Unknown",
            "red_flags_preview": [],
        }

# ---------------------------------------------------------------------------
# Stage 2 — Clause classification
# ---------------------------------------------------------------------------

def analyze_clause(
    text: str,
    contract_type: str = "Unknown",
    weaker_party: str = "Unknown",
    prev_summary: str = "",
) -> ClauseAnalysis:
    settings = get_settings()
    client = _get_client()
    prompt = CLAUSE_PROMPT.format(
        contract_type=contract_type,
        weaker_party=weaker_party,
        prev_summary=prev_summary or "This is the first clause.",
        text=text,
    )
    last_exc = None
    for attempt in range(2):
        try:
            if attempt == 1:
                prompt += "\n\nReturn ONLY the JSON object. No other text."
            raw = _call_llm(client, settings, prompt)
            data = _extract_json(raw)
            category_str = data.get("category", "Moderate Risk")
            data["original_text"] = text
            data["risk_level"] = _category_to_risk_level(category_str)
            data["risk_score"] = _clamp_score_to_category(
                max(0, min(100, int(data.get("risk_score", 50)))),
                category_str,
            )
            data["enforceability_concern"] = bool(data.get("enforceability_concern", False))
            data["what_works_well"] = data.get("what_works_well", "")
            data["affected_party"] = data.get("affected_party", "Both Parties")
            return ClauseAnalysis(**data)
        except Exception as e:
            last_exc = e
            if attempt == 0:
                time.sleep(0.5)
    raise last_exc

# ---------------------------------------------------------------------------
# Stage 3 — Cross-clause contradiction validation
# ---------------------------------------------------------------------------

def _analyze_contradictions(analyzed_clauses: List[ClauseAnalysis]) -> List[ContradictionFinding]:
    settings = get_settings()
    client = _get_client()
    clauses_text = "\n\n".join(
        f"[{c.clause_title}]\n{c.original_text[:600]}"
        for c in analyzed_clauses
    )
    raw = _call_llm(client, settings, CONTRADICTION_PROMPT.format(clauses_text=clauses_text), temperature=0.1)
    result = _extract_json(raw)
    if not isinstance(result, list):
        return []
    findings = []
    for item in result:
        try:
            findings.append(ContradictionFinding(**item))
        except Exception:
            continue
    return findings

# ---------------------------------------------------------------------------
# Stage 4 — Score calibration adjustments
# ---------------------------------------------------------------------------

def _boost_contradiction_clauses(
    analyzed_clauses: List[ClauseAnalysis],
    contradictions: List[ContradictionFinding],
) -> List[ClauseAnalysis]:
    high_titles = {
        title
        for c in contradictions if c.severity == RiskLevel.HIGH
        for title in ([c.clause_a_title] + ([c.clause_b_title] if c.clause_b_title else []))
    }
    result = []
    for clause in analyzed_clauses:
        if clause.clause_title in high_titles and clause.risk_score < 85:
            new_score = min(90, clause.risk_score + 10)
            result.append(clause.model_copy(update={
                "risk_score": new_score,
                "risk_level": RiskLevel.HIGH if new_score > 60 else clause.risk_level,
            }))
        else:
            result.append(clause)
    return result


def _apply_contradiction_score_boost(score: int, contradictions: List[ContradictionFinding]) -> int:
    boost = sum(10 if c.severity == RiskLevel.HIGH else 4 for c in contradictions)
    return min(97, score + boost)


def _derive_risk_level_from_score(score: int) -> RiskLevel:
    if score <= 35:
        return RiskLevel.LOW
    if score <= 70:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH

# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def analyze_contract(clauses: List[Dict], full_text: str = "") -> ContractAnalysis:
    settings = get_settings()
    client = _get_client()

    # Stage 1: detect context
    context = _detect_context(full_text) if full_text else {}
    contract_type = context.get("contract_type", "Unknown")
    weaker_party = context.get("apparent_weaker_party", "Unknown")

    # Stage 2: classify each clause with context + neighbor awareness
    analyzed_clauses: List[ClauseAnalysis] = []
    found_types: set = set()
    prev_summary = ""

    for clause in clauses:
        try:
            result = analyze_clause(
                clause["text"],
                contract_type=contract_type,
                weaker_party=weaker_party,
                prev_summary=prev_summary,
            )
            analyzed_clauses.append(result)
            found_types.add(result.clause_type)
            prev_summary = f"{result.clause_title} ({result.clause_type}): {result.category}"
            time.sleep(4.5)  # stay under Gemini free tier 15 RPM limit
        except Exception:
            placeholder = ClauseAnalysis(
                clause_title=f"Clause {clause['index'] + 1}",
                clause_type="Other",
                original_text=clause["text"],
                category=ClauseCategory.MINOR_IMPROVEMENT,
                risk_level=RiskLevel.LOW,
                risk_score=10,
                affected_party=AffectedParty.BOTH,
                what_works_well="",
                risk_explanation="Analysis unavailable for this clause.",
                suggested_revision="Manual review recommended.",
                negotiation_advice="Consult a legal professional.",
            )
            analyzed_clauses.append(placeholder)
            prev_summary = ""

    # Stage 3: overall summary + quality assessment + missing clause relevance
    clause_summary = "\n".join(
        f"- [{c.category}] {c.clause_title} ({c.clause_type}): score {c.risk_score}"
        for c in analyzed_clauses
    )
    missing_types = [t for t in IMPORTANT_CLAUSE_TYPES if t not in found_types]

    summary_raw = _call_llm(client, settings, SUMMARY_PROMPT.format(
        contract_type=contract_type,
        clause_summary=clause_summary,
        missing_types=", ".join(missing_types) if missing_types else "None",
        found_types=", ".join(found_types) if found_types else "None",
    ))
    summary_data = _extract_json(summary_raw)
    summary_data["overall_risk_score"] = max(0, min(100, int(summary_data.get("overall_risk_score", 50))))

    # Parse quality_summary
    raw_quality = summary_data.get("quality_summary", {})
    quality_summary = ContractQualitySummary(**raw_quality) if raw_quality else None

    # Parse missing_clauses (new structured format, with fallback for plain strings)
    raw_missing = summary_data.get("missing_clauses", [])
    missing_clauses: List[MissingClause] = []
    for item in raw_missing:
        try:
            if isinstance(item, dict):
                missing_clauses.append(MissingClause(**item))
            elif isinstance(item, str):
                missing_clauses.append(MissingClause(
                    clause_type=item,
                    relevance=MissingClauseRelevance.RECOMMENDED,
                    reason="Standard clause not found in document.",
                ))
        except Exception:
            continue

    # Stage 4: contradiction validation
    contradictions: List[ContradictionFinding] = []
    try:
        time.sleep(4.5)
        contradictions = _analyze_contradictions(analyzed_clauses)
    except Exception:
        pass

    # Stage 5: score calibration — boost for contradictions, recalculate level
    if contradictions:
        analyzed_clauses = _boost_contradiction_clauses(analyzed_clauses, contradictions)
        summary_data["overall_risk_score"] = _apply_contradiction_score_boost(
            summary_data["overall_risk_score"], contradictions
        )

    final_score = summary_data["overall_risk_score"]
    final_level = _derive_risk_level_from_score(final_score)

    return ContractAnalysis(
        document_summary=summary_data.get("document_summary", ""),
        analysis_perspective=summary_data.get("analysis_perspective", "Balanced / both parties"),
        overall_risk_score=final_score,
        overall_risk_level=final_level,
        quality_summary=quality_summary,
        final_recommendation=summary_data.get("final_recommendation", ""),
        main_risks=summary_data.get("main_risks", []),
        minor_improvements=summary_data.get("minor_improvements", []),
        best_practice_clauses=summary_data.get("best_practice_clauses", []),
        missing_clauses=missing_clauses,
        contradictions=contradictions,
        clauses=analyzed_clauses,
    )


def answer_question(question: str, context_chunks: List[str]) -> str:
    settings = get_settings()
    client = _get_client()
    context = "\n\n---\n\n".join(context_chunks)
    return _call_llm(client, settings, QA_PROMPT.format(context=context, question=question), temperature=0.3).strip()
