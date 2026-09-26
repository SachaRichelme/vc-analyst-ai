# Evaluation foundation

Step 1 contains **four synthetic development cases**, not a production accuracy
benchmark. Expectations live beside their evidence in `examples/demo/*.json`;
`cases/manifest.json` identifies the evaluation split and annotation owner.

A material claim is any factual assertion or statement that could affect company
identity, mandate qualification, thesis, valuation, risk, or diligence actions.
Unclassified statements default to material. Non-material status requires an explicit
reason (e.g. section heading). `classify_materiality` is a conservative deterministic
policy helper; it cannot determine semantic truth or replace human review.

Human review must distinguish:
- Citation presence: does the reference resolve?
- Support: does the exact passage support the subject, period, value and qualifiers?
- Independence: does corroboration actually have a distinct origin?
- Abstention: are private, unsearched, inaccessible and budget-limited gaps distinguished?
- Usefulness: does the question identify decision-relevant missing evidence?

The default tests verify structure and seeded failure cases, **not** the SPEC's 95%
human support target or professional usefulness. Do not report these fixture tests
as measured research performance. No cost-per-research benchmark exists yet.

Later: annotate a held-out corpus, compare a one-pass baseline using the same scope,
record model/prompt/rate-card versions and human decisions, then report support,
coverage, conflicts, abstention, reviewer time, and cold/warm cost. Paid evaluations
must be opt-in through the central budget gateway. No live evaluator exists in Step 1.
