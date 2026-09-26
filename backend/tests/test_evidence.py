from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.domain.evidence import Claim, MissingReason, NumericValue, TextValue


def data():
    return dict(id=uuid4(), mode="demo", company_id=uuid4(), predicate="revenue",
                value={"kind": "number", "value": "123.45", "unit": "money", "currency": "EUR"},
                statement_class="COMPANY CLAIM", derivation="reported", verification="unreviewed",
                as_of="2026-09-26T12:00:00+02:00")


def test_roundtrip_and_utc():
    claim = Claim(**data())
    assert claim.as_of.hour == 10
    assert str(claim.value.value) == "123.45"
    assert Claim.model_validate_json(claim.model_dump_json()) == claim


@pytest.mark.parametrize("reason", list(MissingReason))
def test_missing_reasons_are_explicit(reason):
    d = data()
    d.update(value=dict(kind="missing", reason=reason, explanation="Not found in reviewed sources"),
             statement_class="UNKNOWN", derivation="unknown")
    assert Claim(**d).value.reason == reason


@pytest.mark.parametrize("change", [
    {"as_of": "2026-09-26T12:00:00"}, {"unexpected": "ignored?"},
    {"statement_class": "FACT", "derivation": "inferred"},
    {"statement_class": "UNKNOWN"},
    {"statement_class": "CALCULATED VALUE", "derivation": "calculated"},
    {"period_start": "2026-01-01T00:00:00Z"},
    {"period_start": "2026-02-01T00:00:00Z", "period_end": "2026-01-01T00:00:00Z"},
])
def test_invalid_claims(change):
    with pytest.raises(ValidationError):
        Claim(**(data() | change))


@pytest.mark.parametrize("value", [True, 0.1, "NaN", "Infinity", ""])
def test_invalid_numbers(value):
    with pytest.raises(ValidationError):
        NumericValue(value=value, unit="EUR")


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_is_not_missing(value):
    with pytest.raises(ValidationError):
        TextValue(value=value)


def test_zero_is_a_real_observation():
    assert NumericValue(value="0", unit="customers").value == 0
