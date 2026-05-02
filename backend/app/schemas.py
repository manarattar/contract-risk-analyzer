from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ClauseCategory(str, Enum):
    BEST_PRACTICE = "Best Practice"
    ACCEPTABLE_STANDARD = "Acceptable Standard"
    MINOR_IMPROVEMENT = "Minor Improvement"
    MODERATE_RISK = "Moderate Risk"
    HIGH_RISK = "High Risk"
    CRITICAL_RISK = "Critical Risk"


class AffectedParty(str, Enum):
    CLIENT = "Client"
    PROVIDER = "Provider"
    BOTH = "Both Parties"


class MissingClauseRelevance(str, Enum):
    ESSENTIAL = "Essential"
    RECOMMENDED = "Recommended"
    OPTIONAL = "Optional / Not Required"


class ClauseAnalysis(BaseModel):
    clause_title: str
    clause_type: str
    original_text: str
    category: ClauseCategory = ClauseCategory.MODERATE_RISK
    risk_level: RiskLevel  # derived from category in analyzer
    risk_score: int = Field(ge=0, le=100)
    affected_party: AffectedParty = AffectedParty.BOTH
    what_works_well: str = ""
    risk_explanation: str
    suggested_revision: str
    negotiation_advice: str
    enforceability_concern: bool = False


class MissingClause(BaseModel):
    clause_type: str
    relevance: MissingClauseRelevance
    reason: str


class ContractQualitySummary(BaseModel):
    overall_legal_structure: str   # Weak / Adequate / Strong
    commercial_balance: str        # One-sided / Mostly Balanced / Balanced
    drafting_clarity: str          # Poor / Adequate / Strong
    enforceability_confidence: str # Low / Medium / High
    negotiation_readiness: str     # Not ready / Needs revision / Ready with minor refinements


class ContradictionFinding(BaseModel):
    clause_a_title: str
    clause_b_title: Optional[str] = None
    contradiction_type: str
    severity: RiskLevel
    description: str
    impact: str


class ContractAnalysis(BaseModel):
    document_summary: str
    analysis_perspective: str = "Balanced / both parties"
    overall_risk_score: int = Field(ge=0, le=100)
    overall_risk_level: RiskLevel
    quality_summary: Optional[ContractQualitySummary] = None
    final_recommendation: str = ""
    main_risks: List[str]
    minor_improvements: List[str] = []
    best_practice_clauses: List[str] = []
    missing_clauses: List[MissingClause] = []
    contradictions: List[ContradictionFinding] = []
    clauses: List[ClauseAnalysis]


class UploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str


class StatusResponse(BaseModel):
    document_id: str
    status: str
    error_message: Optional[str] = None


class QARequest(BaseModel):
    document_id: str
    question: str


class QAResponse(BaseModel):
    answer: str
    sources: List[str]


# ── Comparison schemas ──────────────────────────────────────────────────────

class ClauseStatus(str, Enum):
    IMPROVED = "improved"
    WORSENED = "worsened"
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"


class ClauseComparison(BaseModel):
    clause_type: str
    clause_a: Optional[ClauseAnalysis] = None
    clause_b: Optional[ClauseAnalysis] = None
    risk_delta: int = 0
    status: ClauseStatus


class ContractComparison(BaseModel):
    comparison_id: str
    contract_a_name: str
    contract_b_name: str
    analysis_a: ContractAnalysis
    analysis_b: ContractAnalysis
    overall_delta: int
    winner: str  # "a" | "b" | "equal"
    clause_comparisons: List[ClauseComparison]
    key_differences: List[str]


class CompareStatusResponse(BaseModel):
    comparison_id: str
    status: str
    error_message: Optional[str] = None
