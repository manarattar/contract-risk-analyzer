from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Context(StrictModel):
    contract_type: Literal["Services agreement", "Unknown"] = "Unknown"
    party: str = Field(default="Unknown", min_length=1, max_length=200)
    role: Literal["Customer", "Provider", "Other", "Unknown"] = "Unknown"
    governing_law: str = Field(default="Unknown", min_length=1, max_length=200)
    forum: str = Field(default="Unknown", min_length=1, max_length=200)
    objectives: list[Literal["Liability", "Payment", "Termination", "Intellectual property", "Data handling"]] = Field(default_factory=list, max_length=5)
    confirmed: bool = False


class Decision(StrictModel):
    status: Literal["unreviewed", "accepted", "dismissed", "edited", "escalated"]
    note: str = Field(default="", max_length=4000)
    revision_text: str = Field(default="", max_length=6000)
    version: int = Field(ge=0)


class Question(StrictModel):
    question: str = Field(min_length=3, max_length=1000)


class Compare(StrictModel):
    baseline_id: str = Field(min_length=1, max_length=64)
    revised_id: str = Field(min_length=1, max_length=64)


class CompleteReview(StrictModel):
    revision: int = Field(ge=0)
    acknowledge_incomplete: bool = False


class Annotation(StrictModel):
    block_id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=3, max_length=160)
    note: str = Field(min_length=3, max_length=4000)


class Citation(StrictModel):
    block_id: str
    quote: str = Field(min_length=1, max_length=6000)


class Finding(StrictModel):
    id: str
    title: str = Field(min_length=1, max_length=160)
    explanation: str = Field(min_length=1, max_length=2000)
    impact: Literal["High", "Medium", "Low", "Not assessed"] = "Not assessed"
    uncertainty: str = Field(min_length=1, max_length=1000)
    action: str = Field(min_length=1, max_length=2000)
    suggested_revision: str = Field(default="", max_length=4000)
    revision_caveats: str = Field(default="", max_length=1000)
    citations: list[Citation] = Field(min_length=1, max_length=4)
    business_preference: Literal["Unknown"] = "Unknown"


class Generated(StrictModel):
    block_ids: list[str]
    findings: list[Finding] = Field(max_length=100)
