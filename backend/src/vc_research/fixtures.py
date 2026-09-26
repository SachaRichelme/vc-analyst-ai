"""Validate synthetic evidence graphs without a database or network."""
import hashlib
from pathlib import Path
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .domain.common import Contract, Text
from .domain.evidence import Company, Source, SourceVersion, Passage, Claim, ClaimEvidence


class DocumentFixture(Contract):
    version_id: UUID
    text: Text


class EvaluationExpectation(Contract):
    question: Text
    expected_behavior: Text
    claim_ids: tuple[UUID, ...] = ()
    critical: bool = True


class EvidenceFixture(Contract):
    case_id: Text
    mode: Literal["demo"] = "demo"
    label: Literal["DEMO — synthetic fixture, not live research"] = "DEMO — synthetic fixture, not live research"
    provenance: Text
    license: Literal["CC0-1.0"] = "CC0-1.0"
    companies: tuple[Company, ...]
    sources: tuple[Source, ...]
    versions: tuple[SourceVersion, ...]
    documents: tuple[DocumentFixture, ...]
    passages: tuple[Passage, ...]
    claims: tuple[Claim, ...]
    links: tuple[ClaimEvidence, ...]
    expectations: tuple[EvaluationExpectation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def integrity(self):
        groups = (self.companies, self.sources, self.versions, self.passages, self.claims, self.links)
        records = [record for group in groups for record in group]
        if any(record.mode != "demo" for record in records):
            raise ValueError("fixture cannot mix live and demo records")
        if len({r.id for r in records}) != len(records):
            raise ValueError("duplicate fixture record identity")
        companies = {x.id: x for x in self.companies}
        sources = {x.id: x for x in self.sources}
        versions = {x.id: x for x in self.versions}
        passages = {x.id: x for x in self.passages}
        claims = {x.id: x for x in self.claims}
        documents = {x.version_id: x.text for x in self.documents}
        if len(documents) != len(self.documents) or set(documents) != set(versions):
            raise ValueError("fixture requires one document per source version")
        for version in self.versions:
            if version.source_id not in sources:
                raise ValueError("source version references missing source")
            if sources[version.source_id].retention != "full":
                raise ValueError("full fixture document requires full retention permission")
            if hashlib.sha256(documents[version.id].encode()).hexdigest() != version.content_hash:
                raise ValueError("source content hash does not match")
            if version.previous_version_id is not None:
                old = versions.get(version.previous_version_id)
                if old is None or old.source_id != version.source_id or old.retrieved_at >= version.retrieved_at:
                    raise ValueError("invalid historical version chain")
        for passage in self.passages:
            if passage.source_version_id not in versions:
                raise ValueError("passage references missing version")
            if passage.excerpt not in documents[passage.source_version_id]:
                raise ValueError("evidence excerpt absent from source text")
        for claim in self.claims:
            if claim.company_id not in companies:
                raise ValueError("claim references missing company")
            if not set(claim.premise_claim_ids) <= set(claims):
                raise ValueError("missing inference premise")
            if claim.calculation_id is not None:
                raise ValueError("source-only fixtures cannot reference absent calculation records")
            if claim.supersedes_id is not None:
                old = claims.get(claim.supersedes_id)
                if old is None or old.company_id != claim.company_id or old.predicate != claim.predicate or old.as_of >= claim.as_of:
                    raise ValueError("invalid historical claim chain")
        # Cycle detection is necessary even when every individual reference exists.
        remaining = {c.id: set(c.premise_claim_ids) for c in self.claims}
        while remaining:
            roots = {key for key, deps in remaining.items() if not deps}
            if not roots:
                raise ValueError("cyclic inference premises")
            remaining = {key: deps - roots for key, deps in remaining.items() if key not in roots}
        for link in self.links:
            if link.claim_id not in claims or link.passage_id not in passages:
                raise ValueError("dangling claim/evidence reference")
        for claim in self.claims:
            relations = {link.relationship for link in self.links if link.claim_id == claim.id}
            if claim.verification in {"supported", "partially_supported"} and claim.derivation == "reported" and "supports" not in relations:
                raise ValueError("supported reported claim requires supporting evidence")
            if claim.verification == "conflicted" and not {"supports", "contradicts"} <= relations:
                raise ValueError("conflicted claim needs both sides")
        for expectation in self.expectations:
            if not set(expectation.claim_ids) <= set(claims):
                raise ValueError("annotation references absent claim")
        return self


def load_fixture(path: Path) -> EvidenceFixture:
    return EvidenceFixture.model_validate_json(path.read_text(encoding="utf-8"))
