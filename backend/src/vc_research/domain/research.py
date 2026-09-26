"""Run and output shapes, not a scheduler or research executor."""
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .common import Contract, Count, Mode, Nonnegative, PositiveCount, Record, Text, Timestamp, Versions
from .evidence import MissingReason

Task = Literal["classification", "extraction", "planning", "analysis", "skeptical_review", "memo"]


class Budget(Contract):
    max_search_requests: Count = 0
    max_documents: Count = 0
    max_followup_rounds: Count = 0
    max_llm_calls: Count = 0
    max_strong_model_calls: Count = 0
    max_input_tokens: Count = 0
    max_output_tokens: Count = 0
    max_estimated_cost: Nonnegative = "0"
    max_seconds: PositiveCount = 60
    currency: Literal["USD"] = "USD"

    @model_validator(mode="after")
    def within_total(self):
        if self.max_strong_model_calls > self.max_llm_calls:
            raise ValueError("strong model calls cannot exceed all model calls")
        return self


class Mandate(Contract):
    geographies: tuple[Text, ...]
    stages: tuple[Text, ...]
    sectors: tuple[Text, ...]
    business_models: tuple[Text, ...] = ()
    signal_window: Literal["7d", "30d", "all"] = "30d"


class ResearchRun(Record):
    kind: Literal["sourcing", "quick_scan", "research", "refresh", "memo"]
    profile: Literal["quick_scan", "standard"]
    company_id: UUID | None = None
    parent_run_id: UUID | None = None
    selected_by_analyst: bool = False
    mandate: Mandate | None = None
    as_of: Timestamp
    evidence_cutoff: Timestamp
    generated_at: Timestamp
    budget: Budget = Field(default_factory=Budget)
    versions: Versions
    status: Literal["pending", "running", "complete", "partial", "failed", "cancelled"] = "pending"
    stop_reason: Text | None = None
    reused_claim_ids: tuple[UUID, ...] = ()
    previous_memo_id: UUID | None = None

    @model_validator(mode="after")
    def coherent(self):
        if self.evidence_cutoff > self.as_of or self.as_of > self.generated_at:
            raise ValueError("cutoff <= as_of <= generated time is required")
        if self.kind == "sourcing":
            if self.mandate is None or self.company_id is not None or self.profile != "quick_scan":
                raise ValueError("sourcing requires mandate and quick profile, not selected company")
        elif self.company_id is None:
            raise ValueError("company operation requires company identity")
        if self.kind in {"research", "refresh"} and not self.selected_by_analyst:
            raise ValueError("substantive research requires analyst selection")
        if self.status in {"partial", "failed", "cancelled"} and not self.stop_reason:
            raise ValueError("incomplete runs require a reason")
        return self


class ResearchQuestion(Record):
    run_id: UUID
    question: Text
    importance: Literal["critical", "material", "context"]
    status: Literal["unsearched", "supported", "partial", "conflicted", "unanswered"]
    missing_reason: MissingReason | None = None
    attempts: Count = 0
    next_diligence_action: Text | None = None

    @model_validator(mode="after")
    def missing_state(self):
        if self.status != "supported" and self.missing_reason is None:
            raise ValueError("unresolved question needs an explicit missing reason")
        if self.status == "supported" and self.missing_reason is not None:
            raise ValueError("supported question cannot have a missing-data reason")
        return self


class AnalysisStatement(Record):
    text: Text
    claim_ids: tuple[UUID, ...] = ()
    calculation_ids: tuple[UUID, ...] = ()
    interpretation: bool
    rationale: Text
    # Classification as non-material must be reasoned, never inferred from lack of citations.
    material: bool = True

    @model_validator(mode="after")
    def lineage(self):
        if self.material and not self.claim_ids and not self.calculation_ids:
            raise ValueError("material analysis requires evidence/calculation lineage")
        return self


class ThesisDependency(Record):
    proposition: Text
    support: Literal["supported", "partial", "limited", "unknown", "conflicted"]
    reason: Text
    supporting_claim_ids: tuple[UUID, ...] = ()
    contradicting_claim_ids: tuple[UUID, ...] = ()
    evidence_needed: Text

    @model_validator(mode="after")
    def supported_requires_evidence(self):
        if self.support == "supported" and not self.supporting_claim_ids:
            raise ValueError("supported thesis dependency needs claims")
        if self.support == "conflicted" and not self.contradicting_claim_ids:
            raise ValueError("conflicted thesis dependency needs counterevidence")
        return self


class Thesis(Record):
    current_view: Text
    dependencies: tuple[ThesisDependency, ...] = Field(min_length=1)
    would_strengthen: tuple[Text, ...]
    would_weaken: tuple[Text, ...]

    @model_validator(mode="after")
    def same_mode(self):
        if any(d.mode != self.mode for d in self.dependencies):
            raise ValueError("thesis cannot mix live and demo dependencies")
        return self


class MemoVersion(Record):
    company_id: UUID
    run_id: UUID
    generated_at: Timestamp
    evidence_cutoff: Timestamp
    previous_version_id: UUID | None = None
    status: Literal["draft", "reviewed"] = "draft"
    statements: tuple[AnalysisStatement, ...]
    claim_manifest: tuple[UUID, ...]
    calculation_manifest: tuple[UUID, ...] = ()
    limitations: tuple[Text, ...] = ()

    @model_validator(mode="after")
    def validate_manifest(self):
        if self.evidence_cutoff > self.generated_at:
            raise ValueError("future evidence cutoff")
        if self.previous_version_id == self.id:
            raise ValueError("memo cannot supersede itself")
        for statement in self.statements:
            if statement.mode != self.mode:
                raise ValueError("mixed demo/live statement")
            if not set(statement.claim_ids) <= set(self.claim_manifest):
                raise ValueError("statement claims missing from frozen manifest")
            if not set(statement.calculation_ids) <= set(self.calculation_manifest):
                raise ValueError("statement calculations missing from frozen manifest")
        return self


class Route(Contract):
    task: Task
    provider: Text
    model: Text
    model_revision: Text | None = None
    tier: Literal["cheap", "medium", "strong"]
    prompt_version: Text
    output_schema_version: Text
    max_output_tokens: PositiveCount
    timeout_seconds: PositiveCount
    max_repairs: Literal[0, 1] = 0


class RuntimeConfig(Contract):
    mode: Mode = "demo"
    # Not configurable true in Step 1: credentials cannot unlock spending.
    live_operations_enabled: Literal[False] = False
    routes: tuple[Route, ...] = ()
    budget: Budget = Field(default_factory=Budget)
    global_daily_limit: Nonnegative = "0"
    global_monthly_limit: Nonnegative = "0"
    rate_card_version: Text | None = None

    @model_validator(mode="after")
    def unique_routes(self):
        if len({r.task for r in self.routes}) != len(self.routes):
            raise ValueError("one explicit route per task")
        return self
