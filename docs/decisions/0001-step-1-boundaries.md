# 0001 — Step 1 contracts and safety boundaries

Accepted implementation scope: contracts and offline fixtures only. SPEC.md remains
unchanged and authoritative; the user's later approval supersedes its proposal status.

## Evidence and missing data

Pydantic v2 models reject extra fields, blank values, naive timestamps and invalid
claim/derivation combinations. Record IDs and `mode` are explicit. Timestamps normalize
to UTC. Tagged text/numeric/missing values preserve a genuine zero while requiring a
reason for absence. Decimal strings avoid silent binary floating-point conversion.

Sources, versions, passages, claims, evidence links, calculations, analysis, theses,
memos and corrections are distinct contracts. Source authority belongs on the
claim/evidence link. Published, observed, retrieved and verified timestamps are distinct.
History is represented by predecessor references and frozen memo manifests.

Models are frozen value records with tuple collections. Parse untrusted data through
`model_validate` / `model_validate_json`; Pydantic `model_copy(update=...)` bypasses
validation and is not an ingestion API. Python type hints and frozen models are not
an authorization system. Database FK/transaction integrity is Step 2. Semantic support,
retention enforcement at runtime, citation rendering and human review are later steps.

Synthetic bundle validation additionally checks references, hashes, excerpts, modes,
permissions and both sides of a conflict. It does not certify that real web evidence
is true. Plain HTTP URL types are syntactic contracts, **not** an SSRF-safe fetcher.
No fetcher or unrestricted tool execution exists here.

## Provider and cost boundaries

Search and existing-knowledge protocols are separate; search requests explicitly
require fresh external discovery. Demo search results explicitly say no external
request occurred. Model requests declare task, prompt/schema/model versions and
output limits. Results distinguish success/partial/abstained/failed and preserve data
only in success/partial states. Unreported costs remain null.

Step 1 includes no HTTP/model SDK, credentials loader, paid adapter, retry loop,
worker or scheduler. `live_operations_enabled` can only be false. Fixture adapters
reject live mode even when credentials are present. Step 2 must introduce the central
admission/operations gateway before any live integration; configuration is not a
budget enforcement mechanism by itself.

Route and Budget are small configuration contracts, not a working router/controller.
No model selection, escalation or spending happens automatically. Secrets do not belong
in route records. Default count/spend budgets are zero. Live-mode records are allowed
for future persistence, but live execution is not implemented.

## Reuse and fixtures

Fixtures are exact synthetic replay, not a live cache. Their fingerprints include query
options or model task/input/prompt/schema/revision and exclude run identity. No fallback
to another version or live service is allowed. Unsupported requests abstain.

The SPEC's permission-scoped content and evidence-manifest cache keys will be implemented
later. We preserve the necessary provenance/version fields now without claiming cache,
freshness computation or correction application exists. Relations/corrections retain
original targets, reasoning, actor, time and affected analyses.

## Calculations

The registry resolves an exact formula/version and validates named input contracts.
Inputs require a claim or explicit assumption, never both. Unavailable outputs require
an explicit reason, not zero. The first reviewed formula definition is revenue growth.
Expressions are documentation only and are never evaluated. Numeric execution,
period/currency reconciliation and the financial engine are deliberately not implemented.

## Development

Use Python 3.12+ and a repository-local venv. Only Pydantic and pytest plus their pinned
transitive dependencies are needed. API/server, database, workflow and frontend packages
are deferred until used. The existing frontend scaffold is preserved inactive.

Initial commit uses a one-command local bot identity because Git had no author configured;
no global Git identity was changed. No remote was configured or pushed.

Tests deny DNS and socket connections inside pytest; this is a regression guard, not an
OS sandbox for arbitrary untrusted programs. No production module imports networking
libraries. Dependency installation contacts the package registry; test execution does not.
