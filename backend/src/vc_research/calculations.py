"""Versioned formula/input/output contracts. No formula execution in Step 1."""
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .domain.common import Contract, Number, Record, Text, Timestamp
from .domain.evidence import MissingValue


class FormulaDefinition(Contract):
    name: Text
    version: Text
    description: Text
    inputs: tuple[Text, ...] = Field(min_length=1)
    expression_for_review: Text  # Documentation only: never eval/exec this field.
    output_unit: Text
    preconditions: tuple[Text, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_inputs(self):
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError("duplicate formula input")
        return self


class CalculationInput(Contract):
    name: Text
    value: Number
    unit: Text
    claim_id: UUID | None = None
    assumption: Text | None = None
    as_of: Timestamp

    @model_validator(mode="after")
    def lineage(self):
        if (self.claim_id is None) == (self.assumption is None):
            raise ValueError("input requires exactly one source claim or explicit assumption")
        return self


class CalculationRecord(Record):
    formula: Text
    formula_version: Text
    execution_version: Text
    inputs: tuple[CalculationInput, ...]
    status: Literal["calculated", "unavailable", "invalid"]
    result: Number | None = None
    missing: MissingValue | None = None
    output_unit: Text

    @model_validator(mode="after")
    def result_state(self):
        if self.status == "calculated":
            if self.result is None or self.missing is not None or not self.inputs:
                raise ValueError("calculated result requires inputs and value, no missing state")
        elif self.result is not None or self.missing is None:
            raise ValueError("unavailable/invalid calculation requires reason, not a number")
        return self


class FormulaRegistry:
    def __init__(self, definitions: tuple[FormulaDefinition, ...]):
        self._definitions = {(d.name, d.version): d for d in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("duplicate formula/version")

    def get(self, name: str, version: str) -> FormulaDefinition:
        # Unknown versions raise KeyError, never silently use latest.
        return self._definitions[(name, version)]

    def validate_input_names(self, name: str, version: str, inputs: tuple[CalculationInput, ...]):
        expected = self.get(name, version).inputs
        names = tuple(i.name for i in inputs)
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError("calculation inputs do not match formula definition")


REVENUE_GROWTH = FormulaDefinition(
    name="revenue_growth", version="1.0", description="Growth between comparable revenue periods",
    inputs=("prior_revenue", "current_revenue"),
    expression_for_review="(current_revenue / prior_revenue - 1) * 100",
    output_unit="percent",
    preconditions=("Prior revenue must be positive", "Same currency, entity and revenue definition",
                   "Comparable reporting periods", "Source precision must be preserved"))
