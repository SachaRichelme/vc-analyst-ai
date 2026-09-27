"""Small wire contracts for extraction and analysis; Step 1 remains authoritative."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SECTIONS = ("Team", "Product", "Business Model", "Traction", "Market", "Competition", "Why Now", "Risks", "Critical Unknowns")

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class FinancialCandidate(Strict):
    metric: Literal["revenue", "arr", "gross_profit", "cash", "monthly_net_burn", "enterprise_value", "ebitda"]
    amount: str  # Exact numeric token in quote, not an LLM calculation.
    scale: Literal["units", "thousand", "million", "billion"]
    currency: str
    period: str  # Exact period/as-of text in quote; user verifies comparability.

class ExtractedFact(Strict):
    source_id: str
    section: Literal["Team", "Product", "Business Model", "Traction", "Market", "Competition", "Why Now", "Risks", "Critical Unknowns"]
    quote: str = Field(min_length=8, max_length=600)
    financial: FinancialCandidate | None

class Extraction(Strict):
    company_name: str
    website: str
    identity_resolved: bool
    identity_reason: str
    facts: list[ExtractedFact] = Field(max_length=24)

class Note(Strict):
    text: str = Field(min_length=1, max_length=1000)
    claim_ids: list[str] = Field(max_length=6)
    kind: Literal["INFERENCE", "UNKNOWN"]

class Section(Strict):
    title: Literal["Team", "Product", "Business Model", "Traction", "Market", "Competition", "Why Now", "Risks", "Critical Unknowns"]
    notes: list[Note] = Field(min_length=1, max_length=3)

class Analysis(Strict):
    sections: list[Section] = Field(min_length=9, max_length=9)
    founder_questions: list[Note] = Field(min_length=3, max_length=6)
    bull: Note
    base: Note
    bear: Note

class AnalyzeRequest(Strict):
    company: str = Field(min_length=2, max_length=180)
    mode: Literal["demo", "live"] = "demo"
    confirm_live: bool = False
