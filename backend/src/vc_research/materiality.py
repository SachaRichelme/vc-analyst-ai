"""Conservative review rule, not an LLM judgment or investment score."""
from .domain.common import Contract, Text


class Materiality(Contract):
    material: bool
    reason: Text


def classify_materiality(*, factual: bool, decision_relevant: bool,
                         background_reason: str | None = None) -> Materiality:
    if factual or decision_relevant:
        return Materiality(material=True, reason="Factual or decision-relevant statement requires lineage")
    if not background_reason:
        return Materiality(material=True, reason="Unclassified statements default to material")
    return Materiality(material=False, reason=background_reason)
