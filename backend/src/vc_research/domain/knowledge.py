"""Historical relationships and corrections: records only, not persistence logic."""
from typing import Literal
from uuid import UUID
from pydantic import model_validator
from .common import Record, Text, Timestamp


class CompanyRelation(Record):
    subject_company_id: UUID
    predicate: Literal["founder", "current_executive", "investor", "direct_competitor",
                       "indirect_substitute", "customer", "market", "accelerator"]
    object_company_id: UUID | None = None
    object_entity_id: UUID | None = None
    claim_id: UUID
    effective_from: Timestamp | None = None
    effective_until: Timestamp | None = None
    review_state: Literal["unreviewed", "accepted", "rejected"] = "unreviewed"

    @model_validator(mode="after")
    def object_and_dates(self):
        if (self.object_company_id is None) == (self.object_entity_id is None):
            raise ValueError("relation needs exactly one object")
        if self.object_company_id == self.subject_company_id:
            raise ValueError("company cannot relate to itself in this contract")
        if self.effective_from and self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("invalid relationship interval")
        return self


class AnalystCorrection(Record):
    target_kind: Literal["claim", "relation"]
    target_id: UUID
    replacement: Text
    reason: Text
    actor: Text
    timestamp: Timestamp
    state: Literal["proposed", "accepted", "superseded"] = "proposed"
    affected_analysis_ids: tuple[UUID, ...] = ()
    supersedes_correction_id: UUID | None = None

    @model_validator(mode="after")
    def no_self_reference(self):
        if self.supersedes_correction_id == self.id:
            raise ValueError("correction cannot supersede itself")
        return self
