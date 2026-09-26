from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.domain.research import (Budget, ResearchRun, RuntimeConfig,
    AnalysisStatement, MemoVersion, ResearchQuestion, ThesisDependency)
from vc_research.materiality import classify_materiality


def run_data():
    return dict(id=uuid4(), mode="demo", kind="research", profile="standard", company_id=uuid4(),
                selected_by_analyst=True, as_of="2026-09-26T00:00:00Z",
                evidence_cutoff="2026-09-26T00:00:00Z", generated_at="2026-09-26T00:00:00Z",
                versions=dict(prompt="1", model="fixture", extractor="1", policy="1"))


def test_run_roundtrip():
    run = ResearchRun(**run_data())
    assert ResearchRun.model_validate_json(run.model_dump_json()) == run


@pytest.mark.parametrize("change", [dict(selected_by_analyst=False), dict(company_id=None),
    dict(status="partial"), dict(kind="sourcing"), dict(evidence_cutoff="2026-09-27T00:00:00Z")])
def test_invalid_run(change):
    with pytest.raises(ValidationError): ResearchRun(**(run_data() | change))


def test_partial_preserves_reason():
    assert ResearchRun(**(run_data() | dict(status="partial", stop_reason="Budget exhausted"))).stop_reason


@pytest.mark.parametrize("value", [-1, True, 1.5])
def test_invalid_budget_counts(value):
    with pytest.raises(ValidationError): Budget(max_llm_calls=value)


def test_budget_relationship():
    with pytest.raises(ValidationError): Budget(max_llm_calls=1, max_strong_model_calls=2)


def test_credentials_do_not_enable_live(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    assert RuntimeConfig().live_operations_enabled is False
    with pytest.raises(ValidationError): RuntimeConfig(live_operations_enabled=True)


def test_materiality_defaults_conservative():
    assert classify_materiality(factual=False, decision_relevant=False).material
    assert classify_materiality(factual=True, decision_relevant=False, background_reason="context").material
    assert not classify_materiality(factual=False, decision_relevant=False, background_reason="Section heading").material


def test_question_requires_missing_reason():
    with pytest.raises(ValidationError):
        ResearchQuestion(id=uuid4(), mode="demo", run_id=uuid4(), question="Retention?",
                         importance="critical", status="unanswered")


def test_thesis_support_requires_lineage():
    with pytest.raises(ValidationError):
        ThesisDependency(id=uuid4(), mode="demo", proposition="Customers pay", support="supported",
                         reason="Assertion", evidence_needed="Contracts")


def test_memo_manifest_and_namespace():
    claim_id = uuid4()
    statement = AnalysisStatement(id=uuid4(), mode="demo", text="Company reports growth",
        claim_ids=(claim_id,), interpretation=False, rationale="Company attribution")
    d = dict(id=uuid4(), mode="demo", company_id=uuid4(), run_id=uuid4(),
        generated_at="2026-09-26T00:00:00Z", evidence_cutoff="2026-09-26T00:00:00Z",
        statements=(statement,), claim_manifest=(claim_id,))
    assert MemoVersion(**d).status == "draft"
    with pytest.raises(ValidationError): MemoVersion(**(d | dict(claim_manifest=())))
    with pytest.raises(ValidationError): MemoVersion(**(d | dict(mode="live")))


@pytest.mark.parametrize("change", [dict(max_estimated_cost="-0.01"), dict(max_seconds=0), dict(max_output_tokens=True)])
def test_budget_boundary_regressions(change):
    with pytest.raises(ValidationError): Budget(**change)


def test_routes_have_explicit_limits_and_no_duplicate_task():
    from vc_research.domain.research import Route
    route = Route(task="extraction", provider="future-provider", model="configured-model", tier="cheap",
                  prompt_version="1", output_schema_version="1.0", max_output_tokens=100, timeout_seconds=10)
    assert RuntimeConfig(routes=(route,)).routes == (route,)
    with pytest.raises(ValidationError): RuntimeConfig(routes=(route, route))
    with pytest.raises(ValidationError): Route(**(route.model_dump() | dict(max_repairs=2)))


def test_frozen_records_and_schema_export():
    run = ResearchRun(**run_data())
    with pytest.raises(ValidationError): run.status = "complete"
    assert ResearchRun.model_json_schema()["additionalProperties"] is False
