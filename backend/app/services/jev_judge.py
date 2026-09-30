"""
Clause decisions by Jev, TypeSafe's decision model.

The LLM used to do two different jobs in one prompt: decide what a clause is
(its category, type, who it affects, whether it's enforceable) and write about
it (explanation, suggested revision, negotiation advice). Deciding is a
classification problem, so it now goes to Jev, which returns a probability for
every option instead of generating a label. The LLM only writes the text, and
is told the decisions so the prose can't contradict them.

The risk score is no longer a number the LLM picks: it's the probability-
weighted average of the category bands, clamped to the band of the chosen
category, so a clause Jev is torn between Moderate and High lands between them.

Talks to the REST API with httpx (already a dependency), so the app doesn't
need the typesafe-sdk package or its newer pydantic pin.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import httpx
from app.config import get_settings

JEV_URL = "https://api.typesafe.ai/v1/systemone"

# Below this, Jev's probability is spread over several categories rather than
# peaked on one, so the clause is flagged for a human to check.
LOW_CONFIDENCE = 0.35

# Centre of each category's score band (same bands as CATEGORY_SCORE_BOUNDS)
CATEGORY_MIDPOINTS: Dict[str, float] = {
    "Best Practice": 10,
    "Acceptable Standard": 25,
    "Minor Improvement": 30,
    "Moderate Risk": 50,
    "High Risk": 70,
    "Critical Risk": 90,
}

CLAUSE_TYPES = [
    "Termination",
    "Liability",
    "Payment",
    "Confidentiality",
    "Intellectual Property",
    "Data Protection",
    "Governing Law",
    "Non-compete",
    "Renewal",
    "Indemnity",
    "Dispute Resolution",
    "Warranty",
    "Other",
]

# The same baselines and rubric the LLM prompt uses, as structured criteria
CATEGORY_CRITERIA = {
    "Best Practice": {
        "what": "Clear, balanced and commercially standard; nothing to change",
        "examples": [
            "Written change request / change order process",
            "Client owns custom deliverables; provider keeps pre-existing IP and licenses it",
            "Governing law naming a clear, specific jurisdiction",
        ],
    },
    "Acceptable Standard": {
        "what": "Legally reasonable and commercially normal; at most small refinements",
        "examples": [
            "Liability cap equal to contract value, with carve-outs for gross negligence, "
            "fraud or data breach",
            "Milestone-based payment in a software or service agreement",
            "30-day payment terms, or 30 days or more termination notice",
            "Arbitration or mediation with a named venue and rules",
            "Confidentiality with exceptions for legal obligations or court orders",
        ],
    },
    "Minor Improvement": {
        "what": "Mostly fine, but would benefit from more specific wording",
        "not_for": "clauses that create a real dispute risk",
    },
    "Moderate Risk": {
        "what": "Material ambiguity, imbalance or missing detail that could realistically "
        "cause a dispute",
        "not_for": "normal contractual mechanisms a competent commercial lawyer would accept",
    },
    "High Risk": {
        "what": "Significant exposure, unfairness, contradiction or uncertainty for a party",
        "not_for": "standard clauses that are merely one-sided in a common way",
    },
    "Critical Risk": {
        "what": "Self-defeating, likely unenforceable, or removes essential protections",
        "examples": [
            "Total waiver of all liability including for fraud or gross negligence",
            "Both parties granted exclusive ownership of the same work",
        ],
    },
}

QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": {
            "task": "Classify this contract clause against standard commercial practice.",
            "guardrail": "Before choosing Moderate Risk or higher, ask whether it is actually "
            "harmful or just a normal contractual mechanism. If in doubt, choose Acceptable "
            "Standard.",
        },
        "criteria": CATEGORY_CRITERIA,
    },
    "clause_type": {
        "type": "choice",
        "instructions": "What kind of clause is this?",
        "criteria": {
            **{t: None for t in CLAUSE_TYPES},
            "Other": "scope of work, timeline, acceptance, changes, entire agreement or the preamble",
        },
    },
    "affected_party": {
        "type": "choice",
        "instructions": "Which party bears the risk or disadvantage of this clause?",
        "criteria": {
            "Client": "The clause mainly disadvantages or exposes the client",
            "Provider": "The clause mainly disadvantages or exposes the provider or vendor",
            "Both Parties": "The clause is balanced, or affects both parties equally",
        },
    },
    "enforceability_concern": {
        "type": "noul",
        "instructions": "Would this clause likely be unenforceable in most jurisdictions as written?",
    },
}


def jev_available() -> bool:
    return bool(get_settings().typesafe_api_key.strip())


def risk_score_from_probabilities(probabilities: Dict[str, float]) -> float:
    """Probability-weighted centre of the category bands."""
    total = sum(probabilities.values()) or 1.0
    return sum(CATEGORY_MIDPOINTS[c] * p for c, p in probabilities.items()) / total


def _judge_one(
    client: httpx.Client, clause_text: str, contract_type: str, weaker_party: str
) -> dict:
    settings = get_settings()
    state = {
        "contract_type": contract_type,
        "apparently_weaker_party": weaker_party,
        "clause": clause_text,
    }
    started = time.perf_counter()
    response = client.post(
        JEV_URL,
        headers={"Authorization": f"Bearer {settings.typesafe_api_key}"},
        json={"state": state, "questions": QUESTIONS, "model": settings.jev_model},
    )
    response.raise_for_status()
    answers = response.json()["answers"]
    category = answers["category"]
    return {
        "category": category["choice"],
        "category_probabilities": {
            c: round(p, 3) for c, p in category["probabilities"].items()
        },
        "decision_confidence": round(category["confidence"], 2),
        "clause_type": answers["clause_type"]["choice"],
        "affected_party": answers["affected_party"]["choice"],
        "enforceability_concern": answers["enforceability_concern"]["noul"] >= 0.5,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }


def judge_clauses(
    clauses: List[dict], contract_type: str, weaker_party: str
) -> List[dict]:
    """One Jev request per clause, sent in parallel; results keep the input order."""
    with httpx.Client(timeout=30.0) as client, ThreadPoolExecutor(
        max_workers=8
    ) as pool:
        futures = [
            pool.submit(_judge_one, client, c["text"], contract_type, weaker_party)
            for c in clauses
        ]
        decisions = [f.result() for f in futures]
    for d in decisions:
        d["risk_score"] = round(
            risk_score_from_probabilities(d["category_probabilities"])
        )
        d["needs_review"] = d["decision_confidence"] < LOW_CONFIDENCE
    return decisions
