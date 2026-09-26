from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, Field, model_validator

from .common import Contract, Number, Record, Text, Timestamp


class MissingReason(StrEnum):
    NOT_SEARCHED = "not_searched"
    NOT_FOUND = "not_found_in_reviewed_sources"
    RESTRICTED = "access_restricted"
    BUDGET = "budget_exhausted"
    PROVIDER = "provider_failure"
    CONFLICT = "conflicting_evidence"
    NOT_APPLICABLE = "not_applicable"
    PRIVATE = "requires_private_information"
    STALE = "stale_only"


class TextValue(Contract):
    kind: Literal["text"] = "text"
    value: Text


class NumericValue(Contract):
    kind: Literal["number"] = "number"
    value: Number
    unit: Text
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")] | None = None


class MissingValue(Contract):
    kind: Literal["missing"] = "missing"
    reason: MissingReason
    explanation: Text


ClaimValue = Annotated[TextValue | NumericValue | MissingValue, Field(discriminator="kind")]


class Company(Record):
    name: Text
    website: AnyHttpUrl
    aliases: tuple[Text, ...] = ()
    jurisdiction: Text | None = None
    first_seen_at: Timestamp


class Source(Record):
    url: AnyHttpUrl
    publisher: Text
    source_type: Literal["company", "registry", "investor", "media", "other"]
    origin_group: Text | None = None
    retention: Literal["metadata_only", "excerpt", "full"]
    model_processing_allowed: bool = False
    export_allowed: bool = False
    rights_basis: Text


class SourceVersion(Record):
    source_id: UUID
    title: Text
    content_hash: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    published_at: Timestamp | None = None
    retrieved_at: Timestamp
    observed_at: Timestamp | None = None
    last_checked_at: Timestamp | None = None
    last_verified_at: Timestamp | None = None
    expires_at: Timestamp | None = None
    extractor_version: Text
    previous_version_id: UUID | None = None


class Passage(Record):
    source_version_id: UUID
    excerpt: Text
    locator: Text
    extraction_version: Text


class Claim(Record):
    company_id: UUID
    predicate: Text
    value: ClaimValue
    statement_class: Literal["FACT", "COMPANY CLAIM", "CALCULATED VALUE", "INFERENCE", "ASSUMPTION", "UNKNOWN"]
    derivation: Literal["reported", "calculated", "inferred", "estimated", "unknown"]
    verification: Literal["unreviewed", "supported", "partially_supported", "conflicted", "unsupported"]
    as_of: Timestamp
    observed_at: Timestamp | None = None
    period_start: Timestamp | None = None
    period_end: Timestamp | None = None
    confidence_reasons: tuple[Text, ...] = ()
    calculation_id: UUID | None = None
    premise_claim_ids: tuple[UUID, ...] = ()
    rationale: Text | None = None
    supersedes_id: UUID | None = None

    @model_validator(mode="after")
    def coherent(self):
        missing = isinstance(self.value, MissingValue)
        if missing != (self.statement_class == "UNKNOWN"):
            raise ValueError("UNKNOWN must have a missing value; other classes must have a value")
        expected = {"FACT": {"reported"}, "COMPANY CLAIM": {"reported"},
                    "CALCULATED VALUE": {"calculated"}, "INFERENCE": {"inferred"},
                    "ASSUMPTION": {"estimated"}, "UNKNOWN": {"unknown"}}
        if self.derivation not in expected[self.statement_class]:
            raise ValueError("statement class and derivation disagree")
        if missing and self.verification == "supported":
            raise ValueError("missing information is not a supported observed value")
        if (self.statement_class == "CALCULATED VALUE") != (self.calculation_id is not None):
            raise ValueError("calculated values require calculation lineage only")
        if self.statement_class == "CALCULATED VALUE" and not isinstance(self.value, NumericValue):
            raise ValueError("calculated values must be numeric")
        if self.statement_class in {"ASSUMPTION", "INFERENCE"} and not self.rationale:
            raise ValueError("interpretations require an explicit rationale")
        if self.statement_class == "INFERENCE" and not self.premise_claim_ids:
            raise ValueError("inference requires evidence premises")
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("both period endpoints are required")
        if self.period_start and self.period_end < self.period_start:
            raise ValueError("period ends before it starts")
        if self.id == self.supersedes_id or self.id in self.premise_claim_ids:
            raise ValueError("claim cannot depend on itself")
        return self


class ClaimEvidence(Record):
    claim_id: UUID
    passage_id: UUID
    relationship: Literal["supports", "contradicts", "qualifies"]
    authority_for_claim: Text
    directness: Text
    independence: Literal["independent", "shared_origin", "unknown"]
    reasoning: Text
