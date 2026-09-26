import socket
from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.domain.evidence import TextValue
from vc_research.providers.contracts import (ModelRequest, RequestContext, SearchRequest,
    SearchData, SearchHit, ProviderUsage, Result)
from vc_research.providers.fixtures import (FixtureSearchProvider, FixtureModelProvider,
    ModelFixture, SearchFixture, LiveOperationsDisabled)


def context(mode="demo"):
    return RequestContext(run_id=uuid4(), mode=mode, operation_key="test")


def model_request(**changes):
    return ModelRequest(context=context(), task="classification", model="fixture",
        prompt_version="1", output_schema_version="1.0", input_text="Synthetic company", max_output_tokens=100,
        **changes)


def test_network_guard():
    with pytest.raises(AssertionError, match="network access"):
        socket.create_connection(("example.com", 443))


def test_deterministic_typed_replay():
    req = model_request()
    provider = FixtureModelProvider((ModelFixture(request=req, status="success",
        output_json='{"kind":"text","value":"B2B software"}'),))
    assert provider.complete(req, TextValue) == provider.complete(req, TextValue)
    assert provider.complete(req, TextValue).data.value == "B2B software"
    changed = req.model_copy(update={"prompt_version": "2"})
    assert provider.complete(changed, TextValue).status == "abstained"


def test_malformed_fixture_output_does_not_fallback():
    req = model_request()
    provider = FixtureModelProvider((ModelFixture(request=req, status="success", output_json='{"value":""}'),))
    with pytest.raises(ValidationError): provider.complete(req, TextValue)


def test_live_model_rejected_even_with_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "placeholder")
    req = model_request().model_copy(update={"context": context("live")})
    with pytest.raises(LiveOperationsDisabled): FixtureModelProvider(()).complete(req, TextValue)


def test_fresh_discovery_contract_and_partial_data():
    req = SearchRequest(context=context(), query="European seed software", requested_at="2026-09-26T00:00:00Z", max_results=2)
    hit = SearchHit(url="https://synthetic.example", title="New company", snippet="Synthetic fixture")
    response = Result[SearchData](status="partial", data=SearchData(mode="demo", external_attempted=False,
        fetched_at=req.requested_at, hits=(hit,)), reason="Fixture models source outage",
        usage=ProviderUsage(basis="fixture", estimated_cost="0"))
    provider = FixtureSearchProvider((SearchFixture(request=req, response=response),))
    assert provider.search(req).data.hits == (hit,)
    assert provider.search(req).status == "partial"
    with pytest.raises(LiveOperationsDisabled):
        provider.search(req.model_copy(update={"context": context("live")}))
    assert provider.search(req.model_copy(update={"query": "unknown"})).status == "abstained"


@pytest.mark.parametrize("status", ["abstained", "failed", "partial"])
def test_non_success_needs_reason(status):
    with pytest.raises(ValidationError): Result[TextValue](status=status, usage=ProviderUsage())


def test_search_date_is_not_retrieval_date():
    with pytest.raises(ValidationError):
        SearchHit(url="https://example.com", title="Example", snippet="Example", date_basis="event")


def test_duplicate_fixtures_rejected():
    case = ModelFixture(request=model_request(), status="abstained", reason="Unknown")
    with pytest.raises(ValueError, match="duplicate"): FixtureModelProvider((case, case))


def test_regression_search_fixture_honors_result_limit():
    req = SearchRequest(context=context(), query="software", requested_at="2026-09-26T00:00:00Z", max_results=1)
    hit = SearchHit(url="https://example.com", title="Synthetic", snippet="Synthetic")
    data = SearchData(mode="demo", external_attempted=False, fetched_at=req.requested_at, hits=(hit,hit))
    with pytest.raises(ValidationError, match="result limit"):
        SearchFixture(request=req, response=Result[SearchData](status="success", data=data,
            usage=ProviderUsage(basis="fixture")))
