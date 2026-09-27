"""Decimal-only execution over analyst-reviewed, source-linked inputs."""
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from pydantic import Field
from .models import Strict
from ..calculations import CalculationInput, CalculationRecord

SCALES = {"units": Decimal(1), "thousand": Decimal(1000), "million": Decimal(1_000_000), "billion": Decimal(1_000_000_000)}


def candidate_value(candidate, quote):
    """Reject invented tokens; semantic meaning still requires human review."""
    token = candidate.amount
    if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", token):
        raise ValueError("Not an exact nonnegative monetary token")
    if not re.search(r"(?<![\d.,])" + re.escape(token) + r"(?![\d.,])", quote):
        raise ValueError("Amount is absent from quote")
    if not re.fullmatch(r"[A-Z]{3}", candidate.currency) or candidate.currency not in quote:
        raise ValueError("Explicit ISO currency is required")
    if not candidate.period.strip() or candidate.period not in quote:
        raise ValueError("Period is absent from quote")
    if candidate.scale != "units" and not re.search(r"\b" + candidate.scale + r"\b", quote, re.I):
        raise ValueError("Explicit scale is required")
    value = Decimal(token.replace(",", "")) * SCALES[candidate.scale]
    if value > Decimal("1e16"):
        raise ValueError("Amount exceeds supported range")
    return value


class ReviewRequest(Strict):
    run_id: str
    confirmed: bool = False
    selections: dict[str, str] = Field(default_factory=dict, max_length=6)
    # Explicit analyst assumptions, never silently assigned by the LLM.
    bear_multiple: str = ""
    base_multiple: str = ""
    bull_multiple: str = ""


def initial_finance(candidates):
    return {"status": "review_required" if candidates else "unavailable", "calculations": [],
            "reason": ("Source-linked financial candidates require analyst verification of metric, currency, period and comparability. No calculations yet."
                       if candidates else "Not publicly available in reviewed sources: sufficient reliable, comparable financial inputs. No values were invented."),
            "valuation": "Valuation withheld: no reviewed comparable multiples or enterprise-value/revenue pair.",
            "dcf": "DCF withheld: no analyst-approved cash-flow forecast, discount rate or terminal assumptions. Public traction and funding do not support a DCF."}


def calculate(candidates, review, mode):
    if not review.confirmed:
        raise ValueError("Confirm source, units and period comparability before calculation")
    by_id = {c["id"]: c for c in candidates if not c.get("conflicted")}
    allowed = {"prior_revenue": "revenue", "current_revenue": "revenue", "gross_profit": "gross_profit",
               "cash": "cash", "monthly_net_burn": "monthly_net_burn", "enterprise_value": "enterprise_value"}
    chosen = {}
    for role, claim_id in review.selections.items():
        if role not in allowed or claim_id not in by_id or by_id[claim_id]["metric"] != allowed[role]:
            raise ValueError("Selection is not a compatible, non-conflicted financial input")
        chosen[role] = by_id[claim_id]
    if len({c["id"] for c in chosen.values()}) != len(chosen):
        raise ValueError("A financial observation cannot fill two different roles")
    now = datetime.now(timezone.utc)
    records, refusals = [], []

    def execute(name, names, unit, expression, function, same_period=False):
        if not all(n in chosen for n in names):
            refusals.append(f"{name}: required reviewed inputs missing")
            return
        data = [chosen[n] for n in names]
        if len({d["currency"] for d in data}) != 1:
            raise ValueError("Mixed currencies are not comparable; no implicit FX conversion")
        if same_period and len({d["period"] for d in data}) != 1:
            raise ValueError("Gross profit and revenue must cover the same reported period")
        values = [Decimal(d["value"]) for d in data]
        if values[-1] <= 0:
            refusals.append(f"{name}: denominator must be positive")
            return
        record = CalculationRecord(id=uuid4(), mode=mode, formula=name, formula_version="1.0",
            execution_version="demo-finance-1", status="calculated", result=function(*values),
            output_unit=unit, inputs=tuple(CalculationInput(name=n, value=Decimal(d["value"]),
                unit=d["currency"], claim_id=d["claim_uuid"], as_of=now) for n, d in zip(names, data)))
        records.append({"record": record.model_dump(mode="json"), "formula": expression,
                        "claim_ids": [d["id"] for d in data]})

    if "current_revenue" in chosen and "prior_revenue" in chosen and chosen["current_revenue"]["period"] == chosen["prior_revenue"]["period"]:
        raise ValueError("Growth requires two different, comparable reporting periods")
    execute("Revenue growth", ["current_revenue", "prior_revenue"], "percent", "(current / prior - 1) × 100", lambda c,p:(c/p-1)*100)
    execute("Gross margin", ["gross_profit", "current_revenue"], "percent", "gross profit / revenue × 100", lambda g,r:g/r*100, True)
    execute("Runway", ["cash", "monthly_net_burn"], "months", "cash / monthly net burn", lambda c,b:c/b)
    execute("Observed EV / revenue", ["enterprise_value", "current_revenue"], "multiple", "enterprise value / revenue", lambda e,r:e/r)
    multiples = [review.bear_multiple, review.base_multiple, review.bull_multiple]
    if any(multiples):
        if not all(multiples) or "current_revenue" not in chosen:
            raise ValueError("Scenarios need all three explicit multiples and reviewed revenue")
        try:
            parsed = [Decimal(v) for v in multiples]
            if any(not v.is_finite() or not Decimal(0) < v <= Decimal(100) for v in parsed) or parsed != sorted(parsed):
                raise ValueError("Multiples must be ordered bear ≤ base ≤ bull, positive and at most 100")
        except InvalidOperation as exc:
            raise ValueError("Multiples must be decimal numbers") from exc
        revenue = chosen["current_revenue"]
        for label, multiple in zip(("Bear", "Base", "Bull"), parsed):
            record = CalculationRecord(id=uuid4(), mode=mode, formula=f"{label} revenue-multiple scenario", formula_version="1.0",
                execution_version="demo-finance-1", status="calculated", result=Decimal(revenue["value"])*multiple,
                output_unit=revenue["currency"] + " enterprise value", inputs=(
                    CalculationInput(name="revenue", value=Decimal(revenue["value"]), unit=revenue["currency"], claim_id=revenue["claim_uuid"], as_of=now),
                    CalculationInput(name="multiple", value=multiple, unit="multiple", assumption="Analyst-entered illustrative revenue multiple; not a sourced comparable", as_of=now)))
            records.append({"record": record.model_dump(mode="json"), "formula": "reviewed revenue × analyst-assumed multiple", "claim_ids": [revenue["id"]]})
    result = initial_finance(candidates)
    result.update(status="calculated" if records else "unavailable", calculations=records,
                  reason=("Python Decimal calculations on analyst-reviewed reported inputs. Precision of source inputs still limits the results."
                          if records else "No calculation performed: sufficient reviewed inputs with positive denominators were not supplied."), unavailable=refusals)
    if any("scenario" in r["record"]["formula"] for r in records):
        result["valuation"] = "Illustrative enterprise-value sensitivities only. Multiples are analyst assumptions, not market comps or a recommended price; no debt/cash bridge to equity value."
    elif any(r["record"]["formula"] == "Observed EV / revenue" for r in records):
        result["valuation"] = "Observed company multiple only. Comparable-company selection and date/metric normalization have not been established; no fair-value conclusion."
    return result
