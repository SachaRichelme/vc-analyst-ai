import json
from pathlib import Path
from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.fixtures import EvidenceFixture, load_fixture
from vc_research.providers.fixtures import (SearchFixture, ModelFixture, FixtureSearchProvider, FixtureModelProvider)
from vc_research.domain.evidence import TextValue

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "examples/demo"


@pytest.mark.parametrize("case", ["supported", "sparse", "conflicted", "refresh"])
def test_fixture_graphs(case):
    fixture = load_fixture(DEMO / f"{case}.json")
    assert fixture.mode == "demo"
    assert EvidenceFixture.model_validate_json(fixture.model_dump_json()) == fixture


@pytest.mark.parametrize("mutation", ["reference", "hash", "excerpt", "namespace", "duplicate", "support", "retention"])
def test_invalid_graphs(mutation):
    d = json.loads((DEMO / "supported.json").read_text())
    if mutation == "reference": d["links"][0]["claim_id"] = str(uuid4())
    if mutation == "hash": d["versions"][0]["content_hash"] = "0" * 64
    if mutation == "excerpt": d["passages"][0]["excerpt"] = "Fabricated quote"
    if mutation == "namespace": d["claims"][0]["mode"] = "live"
    if mutation == "duplicate": d["claims"].append(d["claims"][0])
    if mutation == "support": d["links"] = []
    if mutation == "retention": d["sources"][0]["retention"] = "metadata_only"
    with pytest.raises(ValidationError): EvidenceFixture.model_validate(d)


def test_conflict_both_sides_required():
    d = json.loads((DEMO / "conflicted.json").read_text())
    d["links"] = d["links"][:1]
    with pytest.raises(ValidationError): EvidenceFixture.model_validate(d)


def test_refresh_keeps_history():
    case = load_fixture(DEMO / "refresh.json")
    assert len(case.versions) == 2
    assert case.claims[1].supersedes_id == case.claims[0].id
    assert case.claims[1].as_of > case.claims[0].as_of


def test_committed_transcripts_replay():
    search = SearchFixture.model_validate_json((DEMO / "search.json").read_text())
    result = FixtureSearchProvider((search,)).search(search.request)
    known = load_fixture(DEMO / "supported.json")
    assert result.data.hits[0].url not in {c.website for c in known.companies}
    assert result.data.external_attempted is False  # demo must not masquerade as live sourcing
    model = ModelFixture.model_validate_json((DEMO / "model.json").read_text())
    assert FixtureModelProvider((model,)).complete(model.request, TextValue).data.value == "B2B software"


def test_regression_history_cannot_run_backwards():
    d = json.loads((DEMO / "refresh.json").read_text())
    d["claims"][1]["as_of"] = "2025-01-01T00:00:00Z"
    with pytest.raises(ValidationError, match="historical claim"):
        EvidenceFixture.model_validate(d)


def test_regression_inference_cycles_rejected():
    d = json.loads((DEMO / "supported.json").read_text())
    first = d["claims"][0]
    second = dict(first, id=str(uuid4()))
    for claim in (first, second):
        claim.update(statement_class="INFERENCE", derivation="inferred", rationale="Inference", verification="unreviewed")
    first["premise_claim_ids"] = [second["id"]]
    second["premise_claim_ids"] = [first["id"]]
    d["claims"].append(second)
    with pytest.raises(ValidationError, match="cyclic"):
        EvidenceFixture.model_validate(d)
