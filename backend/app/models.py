from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Severity = Literal["low", "medium", "high"]


class Clause(BaseModel):
    id: str
    index: int
    heading: str
    text: str
    page: int
    char_start: int
    char_end: int


class Flag(BaseModel):
    flag_id: str
    severity: Severity
    category: str
    matched_text: str
    explanation_template: str
    suggestion_template: str


class Explanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plain_summary: str = Field(min_length=1, max_length=700)
    who_benefits: Literal["tenant", "landlord", "freelancer", "client", "balanced", "unclear"]
    risk_level: Severity
    why_it_matters: str = Field(min_length=1, max_length=700)
    what_to_ask_or_negotiate: str = Field(min_length=1, max_length=700)
    evidence_quote: str = Field(max_length=1000)
