from uuid import uuid4
import pytest
from pydantic import ValidationError
from vc_research.calculations import (FormulaRegistry, REVENUE_GROWTH,
    CalculationInput, CalculationRecord)


def inp(name="prior_revenue", **changes):
    return CalculationInput(**(dict(name=name, value="100.00", unit="EUR",
        claim_id=uuid4(), as_of="2026-09-26T00:00:00Z") | changes))


def test_registry_exact_versions_and_names():
    r = FormulaRegistry((REVENUE_GROWTH,))
    r.validate_input_names("revenue_growth", "1.0", (inp(), inp("current_revenue")))
    with pytest.raises(KeyError): r.get("revenue_growth", "2.0")
    with pytest.raises(ValueError): r.validate_input_names("revenue_growth", "1.0", (inp(),))
    with pytest.raises(ValueError): FormulaRegistry((REVENUE_GROWTH, REVENUE_GROWTH))


@pytest.mark.parametrize("changes", [dict(claim_id=None), dict(assumption="Estimate")])
def test_input_lineage_is_exclusive(changes):
    with pytest.raises(ValidationError): inp(**changes)


def test_missing_result_is_not_zero():
    d = dict(id=uuid4(), mode="demo", formula="revenue_growth", formula_version="1.0", execution_version="fixture",
             inputs=(), status="unavailable", output_unit="percent",
             missing=dict(reason="not_found_in_reviewed_sources", explanation="Revenue not disclosed"))
    assert CalculationRecord(**d).result is None
    with pytest.raises(ValidationError): CalculationRecord(**(d | dict(result="0")))
