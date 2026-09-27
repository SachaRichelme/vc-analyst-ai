"""Offline checks of the interrupted backend only; not browser/live acceptance."""
from decimal import Decimal
from uuid import uuid4

import pytest

from vc_research.demo.finance import ReviewRequest, calculate, candidate_value
from vc_research.demo.live import LiveProvider, RunError
from vc_research.demo.models import Analysis, Extraction, FinancialCandidate, SECTIONS
from vc_research.demo.pipeline import run_analysis, validate_analysis


class FakeProvider:
    """Test-local synthetic responses, never usable as a live provider."""
    def research(self, company):
        return [{"id": "S1", "url": "https://fixture.example/", "title": "Synthetic company",
                 "text": "We sell software subscriptions to small businesses.",
                 "retrieved_at": "2026-09-26T12:00:00+00:00", "published_at": None,
                 "coverage": "synthetic fixture"}]

    def extract(self, company, sources):
        return Extraction(company_name="Synthetic company", website="https://fixture.example/",
            identity_resolved=True, identity_reason="Synthetic identity",
            facts=[{"source_id": "S1", "section": "Product", "quote": sources[0]["text"], "financial": None}])

    def analyze(self, company, claims):
        unknown = {"text": "Not found in reviewed sources; ask the founder for evidence.", "kind": "UNKNOWN", "claim_ids": []}
        return Analysis.model_validate({"sections": [{"title": section, "notes": [unknown]} for section in SECTIONS],
            "founder_questions": [unknown] * 3, "bull": unknown, "base": unknown, "bear": unknown})

    def usage(self):
        return {"searches": 0, "model_calls": 0}


def live():
    # Explicitly fake keys; autouse socket guard still denies all external I/O.
    return LiveProvider(env={"VC_ENABLE_LIVE": "true", "OPENAI_API_KEY": "fake", "TAVILY_API_KEY": "fake"})


def test_partial_pipeline_preserves_contracts_and_abstains_without_financials():
    report = run_analysis("https://fixture.example", FakeProvider(), "demo")
    assert report["financials"]["status"] == "unavailable"
    assert len(report["analysis"]["sections"]) == 9
    assert report["evidence_graph"]["claims"][0]["statement_class"] == "COMPANY CLAIM"
    assert report["evidence_graph"]["claims"][1]["value"]["reason"] == "not_found_in_reviewed_sources"
    assert report["evidence"][0]["claim_uuid"] == report["evidence_graph"]["claim_evidence"][0]["claim_id"]
    assert "SYNTHETIC FIXTURE" in report["memo_markdown"]
    assert "https://fixture.example/" in report["memo_markdown"]


def test_unsupported_quote_stops_before_analysis():
    provider = FakeProvider()
    extract = provider.extract
    provider.extract = lambda company, sources: extract(company, sources).model_copy(update={
        "facts": [extract(company, sources).facts[0].model_copy(update={"quote": "Fabricated traction claim"})]})
    provider.analyze = lambda *args: pytest.fail("Must not analyze rejected evidence")
    with pytest.raises(RunError, match="No exact"):
        run_analysis("https://fixture.example", provider, "demo")


def test_identity_mismatch_stops_pipeline():
    with pytest.raises(RunError, match="does not match"):
        run_analysis("https://different.example", FakeProvider(), "demo")


@pytest.mark.parametrize("kind,ids", [("INFERENCE", []), ("INFERENCE", ["C999"]), ("UNKNOWN", ["C999"])])
def test_invalid_citations_are_rejected(kind, ids):
    analysis = FakeProvider().analyze("fixture", [])
    analysis.bull.kind, analysis.bull.claim_ids = kind, ids
    with pytest.raises(RunError, match="unsupported citation"):
        validate_analysis(analysis, [{"id": "C1"}])


def test_live_requires_explicit_enablement_and_both_keys():
    with pytest.raises(RunError, match="disabled"):
        LiveProvider(env={"OPENAI_API_KEY": "fake", "TAVILY_API_KEY": "fake"})
    with pytest.raises(RunError, match="both API keys"):
        LiveProvider(env={"VC_ENABLE_LIVE": "true"})


def test_admission_limits_and_failed_request_not_retried(monkeypatch):
    provider = live()
    attempts = []
    def fail(*args):
        attempts.append(1)
        raise RunError("Synthetic provider failure")
    monkeypatch.setattr(provider, "post", fail)
    with pytest.raises(RunError, match="Synthetic"):
        provider.research("fixture")
    assert len(attempts) == provider.searches == 1
    provider.reserve("search", .01)
    provider.reserve("search", .01)
    with pytest.raises(RunError, match="limit"):
        provider.reserve("search", .01)
    for _ in range(2):
        provider.reserve("model", .01)
    with pytest.raises(RunError, match="limit"):
        provider.reserve("model", .01)
    with pytest.raises(RunError, match="limit"):
        live().reserve("search", .21)


def test_fresh_search_invocations_and_deduplication(monkeypatch):
    calls = []
    def search(*args):
        calls.append(args)
        return {"results": [{"url": "https://fixture.example/", "content": "Synthetic search excerpt", "title": "Fixture"}]}
    for _ in range(2):
        provider = live()
        monkeypatch.setattr(provider, "post", search)
        sources = provider.research("fixture")
        assert len(sources) == 1
        assert sources[0]["coverage"] == "search excerpt only"
    assert len(calls) == 6  # Every run searches again; no real network used.
    assert all(c[1]["search_depth"] == "basic" and not c[1]["auto_parameters"] for c in calls)


def observation(id, value, period="2025", currency="USD"):
    return {"id": id, "claim_uuid": str(uuid4()), "metric": "revenue", "value": value,
            "period": period, "currency": currency, "conflicted": False}


def test_finance_review_gate_exact_growth_and_scenario_lineage():
    candidates = [observation("C1", "100", "2024"), observation("C2", "125")]
    review = ReviewRequest(run_id="test", selections={"prior_revenue": "C1", "current_revenue": "C2"},
                           bear_multiple="2", base_multiple="3", bull_multiple="4")
    with pytest.raises(ValueError, match="Confirm"):
        calculate(candidates, review, "demo")
    result = calculate(candidates, review.model_copy(update={"confirmed": True}), "demo")
    records = [c["record"] for c in result["calculations"]]
    assert [Decimal(r["result"]) for r in records] == [Decimal(25), Decimal(250), Decimal(375), Decimal(500)]
    assert records[1]["inputs"][1]["assumption"]
    assert records[0]["inputs"][0]["claim_id"] == candidates[1]["claim_uuid"]


@pytest.mark.parametrize("change,error", [({"currency": "EUR"}, "currencies"), ({"period": "2024"}, "different"), ({"conflicted": True}, "non-conflicted")])
def test_finance_rejects_incomparable_or_conflicted_inputs(change, error):
    candidates = [observation("C1", "100", "2024"), {**observation("C2", "125"), **change}]
    with pytest.raises(ValueError, match=error):
        calculate(candidates, ReviewRequest(run_id="test", confirmed=True,
            selections={"prior_revenue": "C1", "current_revenue": "C2"}), "demo")


def test_missing_and_zero_denominator_do_not_claim_success():
    review = ReviewRequest(run_id="test", confirmed=True)
    assert calculate([], review, "demo")["reason"].startswith("No calculation performed")
    review.selections = {"prior_revenue": "C1", "current_revenue": "C2"}
    result = calculate([observation("C1", "0", "2024"), observation("C2", "125")], review, "demo")
    assert result["status"] == "unavailable"
    assert not result["calculations"]


def test_financial_tokens_require_explicit_source_units_and_currency():
    candidate = FinancialCandidate(metric="revenue", amount="12.5", scale="million", currency="USD", period="2025")
    assert candidate_value(candidate, "Revenue was USD 12.5 million in 2025") == Decimal("12500000")
    for quote in ("Revenue was USD 2.5 million in 2025", "Revenue was $12.5 million in 2025", "Revenue was USD 12.5 in 2025"):
        with pytest.raises(ValueError):
            candidate_value(candidate, quote)
