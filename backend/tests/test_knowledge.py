from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.domain.knowledge import CompanyRelation, AnalystCorrection


def test_relation_requires_exactly_one_object():
    d = dict(id=uuid4(), mode="demo", subject_company_id=uuid4(), predicate="indirect_substitute", claim_id=uuid4())
    with pytest.raises(ValidationError): CompanyRelation(**d)
    with pytest.raises(ValidationError): CompanyRelation(**d, object_company_id=uuid4(), object_entity_id=uuid4())
    assert CompanyRelation(**d, object_company_id=uuid4()).review_state == "unreviewed"


def test_correction_retains_target_and_reason():
    d = dict(id=uuid4(), mode="demo", target_kind="relation", target_id=uuid4(),
        replacement="indirect_substitute", reason="Different buyer and workflow", actor="Local analyst",
        timestamp="2026-09-26T00:00:00Z", state="accepted", affected_analysis_ids=(uuid4(),))
    c = AnalystCorrection(**d)
    assert AnalystCorrection.model_validate_json(c.model_dump_json()) == c
    with pytest.raises(ValidationError): AnalystCorrection(**(d | dict(reason="")))
