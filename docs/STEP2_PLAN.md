# Proposed Step 2 — Minimal Runtime and Persistence

> SUPERSEDED by the user's demo-first vertical-slice instruction. Retained as historical
> planning only; do not implement its PostgreSQL/runtime milestones before the browser demo.
> Current recovery status and the minimal remaining path: [RECOVERY_REPORT.md](RECOVERY_REPORT.md).

Status: planning only; awaiting approval. No Step 2 implementation has begun.

## 1. Approved checkpoint

Step 1 commit: `c6c61bc` (`feat: add approved Step 1 contracts and offline fixtures`).
All 79 tests passed before the commit. No remote is configured and nothing was pushed.
The local bot identity remains the same as the initial commit; global Git configuration was not changed.

The product adjustment changes the remaining roadmap, not the value of the existing code. SPEC.md v2 is the proposed authoritative scope; docs/archive/SPEC-v1-approved.md preserves the prior specification exactly. The archived file and earlier implementation report are historical, not competing instructions.

## 2. Existing Step 1 contract review

| Existing file/contracts | Decision | Rationale / when to extend |
|---|---|---|
| `domain/common.py`: Contract, Record, Versions, Decimal and timestamp types | Keep unchanged | Typed IDs, modes, schema versions, precise values and UTC remain necessary |
| `domain/evidence.py`: Company, Source, SourceVersion, Passage, Claim, ClaimEvidence | Keep unchanged | Separate evidence entities and claim-specific authority remain central, even with a smaller database |
| `MissingReason`, tagged claim values | Keep unchanged | Preserve all nine missing states and a real observed zero |
| `ResearchRun`, Mandate, Budget | Keep for Step 2 | Runtime row timestamps/state can wrap the immutable run snapshot; no need to rewrite the public contract for SQL columns |
| `ResearchQuestion`, AnalysisStatement, Thesis/Dependency, MemoVersion | Keep unchanged | Still needed for VC judgment, missing information and cited memo input manifests |
| `Route`, Versions | Keep unchanged | One provider and fewer workflow stages still benefit from task limits and explicit versions |
| `RuntimeConfig` | Keep live-disabled through Step 2 | Step 3 needs a deliberate opt-in configuration extension; do not relax Literal[False] while only fixtures exist |
| `providers/contracts.py`: SearchProvider, ExistingKnowledge | Keep unchanged | Fresh external search must remain distinct from querying local memory |
| `ModelProvider`, ModelRequest, Result | Keep unchanged now | Exact typed output, partial/failure/abstention remain appropriate; central runtime gate wraps adapters |
| `ProviderUsage` | Keep with explicit interpretation | When basis is unreported, default zero counters are not confirmed zero usage; preserve conservative reservation. Normalize missing live usage explicitly at Step 3 |
| Fixture adapters, fingerprints, fixture graph validation | Keep unchanged | They are exact demo replay, not the future live cache or a real source-fetcher |
| `CompanyRelation`, AnalystCorrection | Retain dormant | Do not create history tables, propagation services or a correction UI merely because these types exist |
| Historical predecessor IDs and optional reuse fields | Retain; use minimally | Saved citations/history can remain intact without timeline analysis or a general knowledge graph |
| RuntimeConfig monthly limit | Retain future-facing | Default zero/unconfigured; reject a nonzero unsupported limit rather than pretending it is enforced; daily protection is sufficient initially |
| CalculationInput/Record, FormulaRegistry, REVENUE_GROWTH | Keep unchanged for Step 2 | Useful foundation; do not implement finance in this runtime step |
| Materiality helper, existing tests and all fixtures | Keep unchanged | Evidence reliability has not been deprioritized |

### Genuine extensions, at their implementation boundary

**Now:** no Step 1 source modification is required. This turn changes documentation only.

**Step 2:** add small persistence/runtime contracts instead of refactoring evidence: operation state/reservation/observed usage, run lifecycle timestamps, runtime-local settings, and artifact/cache policy. Existing ResearchRun is the typed immutable request/snapshot, not a job lease. `generated_at` remains the snapshot generation time; database `started_at`/`finished_at` represent execution. Completed output/memo has its own generation/cutoff time. Reject changed input under the same idempotency key. No SQL coercion of missing values to zero.

The existing Budget lacks document byte limits; add bounded response/aggregate byte limits to the new runtime settings and enforce them when retrieval is introduced. Do not call such future enforcement implemented in Step 2 if no real fetcher exists.

**Step 3:** explicitly evolve live configuration only after the gate is tested. Enabling requires an intentional local setting, configured nonzero limits, a usable rate card and a registered live adapter—not merely a credential. Credentials remain server-side and never enter stored configuration snapshots. Normalize unknown usage as unknown; test that unreported default counters never release a possibly billed reservation. Existing fixture adapters continue rejecting live mode.

**Step 4:** CalculationInput currently has only a unit and as-of date; that is insufficient for reliable cohort, period and currency comparisons. Add typed financial context (currency, period bounds, metric/accounting basis, entity, cohort where relevant) and assumption metadata with reasons and provenance. Introduce method eligibility, scenario assumptions and sensitivity/valuation result contracts composing calculation records. Do not overload a single scalar CalculationRecord into a DCF table. Version these new contracts, preserve existing fixtures, and test eligibility and refusing missing/incompatible inputs before implementing formulas.

No new autonomous finance agent/task is needed for arithmetic. Interpretation can use the existing analysis task. Historical relationship/correction contracts need no modification merely because they are dormant.

## 3. Exact Step 2 scope

### 2.1 Local PostgreSQL and setup

- Add one Docker Compose PostgreSQL service, bound to `127.0.0.1`, with a documented persistent local volume and readiness check. No cloud resources.
- Add SQLAlchemy, Alembic and one PostgreSQL driver only, with locked dependency updates.
- Document setup, migration, status, stop/start and explicit destructive-reset warnings in README. Normal stop must preserve data.
- Separate development and test database names. Integration tests must reject an unrecognized/non-test target before resetting any schema.
- The existing pure offline tests still run without Docker/PostgreSQL. A separate explicit integration test command requires local PostgreSQL and fails clearly if it is unavailable.

### 2.2 Minimal schema and repositories

Implement exactly the nine logical tables in SPEC section B: companies, source_documents, source_versions, evidence_passages, claims, claim_evidence, research_runs, operations, memo_versions.

- Use relational columns for IDs/FKs, mode, safe canonical-domain identity, indexed lookup keys, time/status and numeric cost fields.
- Store remaining versioned Pydantic payloads in validated JSONB. Evidence objects remain separate rows with FK integrity.
- Use composite mode/ID references or an equivalently tested database constraint so demo rows cannot link to live rows.
- Exact domain/known identifier matches can reuse a company. Name similarity does not auto-merge. Keep ambiguous identities distinct.
- Persist a fixture evidence bundle transactionally; reject duplicate/conflicting IDs, dangling references and mismatched namespace without partial writes.
- Load bundles and saved run outputs with contract validation. A corrupt row yields an explicit error, not silent partial deserialization.
- Preserve source/claim snapshots referenced by saved memos. No automatic garbage collection or sophisticated version history.
- Persist generic typed run-output/memo snapshots for later steps; do not generate memos or implement their future analytical content now.

Indexes are limited to actual lookup paths: mode+domain, source URL, document+hash, claim company/as-of, run status/time, operation key/cache key/run, memo company/run.

### 2.3 Explicit sequential runtime

Provide a small local command entry point to import/show fixture evidence, start a fixture-only run, inspect its result/operations and cancel/report interrupted work. This is a developer harness, not a research product UI.

- Only one explicitly invoked runner may execute at a time. Hold a PostgreSQL advisory lock on a dedicated connection while it runs; a second invocation returns a clear busy error rather than entering a queue.
- Use short database transactions around state/operation updates. Do not hold a row transaction across provider calls.
- Execute a bounded list of ordinary Python tasks synchronously/sequentially. No cron, polling worker, scheduler, queue or autonomous loop.
- Persist pending/running/complete/partial/failed/cancelled state and stop reason. Partial output remains accessible.
- Handle Ctrl+C and explicit cancellation between operations. An in-flight attempt remains potentially billed until its outcome is known.
- On restart/next explicit invocation, after exclusive-lock acquisition, identify interrupted rows, mark partial and retain uncertain reservations. Never automatically repeat work or resume an old run.
- If the lock database connection is lost, fail closed before any new external operation. An already in-flight call may still complete or be charged.

No long HTTP request is needed in Step 2. The same runner services can later be invoked through a local FastAPI interface with explicit run controls. No separate distributed worker is implied.

### 2.4 Simple operation and cost guard

A single service mediates provider operations; future application code must not invoke paid adapters directly.

Admission order:

1. Validate mode, supported task/provider configuration and request identity.
2. Check a permitted exact cache hit. A hit needs no paid call; fresh-search obligations are never satisfied by a prior run's search cache.
3. Require explicit per-run limits and the operator's daily ceiling for billable execution. Live operations remain unavailable in Step 2 regardless.
4. Bound tokens/time/calls and estimate conservative cost using a versioned rate card (synthetic test rate cards only in Step 2).
5. Transactionally persist an operation reservation and ensure spent + unresolved reservations + proposed work stays within limits. Include unresolved reservations from earlier days/runs in the remaining-liability guard so midnight/restart cannot clear unknown charges.
6. Execute the injected fixture/fake provider once.
7. Persist successful output or an explicit partial/failure/unknown outcome. Reconcile known usage once; retain the full conservative reservation for an ambiguous billed result.

Counts, tokens, strong-model calls, elapsed deadline and estimated spend must all be enforced, not just the monetary field. Default retries are zero. A later allowed retry is a separately counted/reserved attempt; never silently retry an unknown billed result. If reported cost exceeds its estimate, record the discrepancy and block subsequent paid operations until inspected. No negative reservation release or double reconciliation.

An idempotency key guarantees no repeated locally committed operation; it cannot guarantee exactly-once behavior at a remote vendor. The runtime explicitly acknowledges that limitation.

Basic reporting: search/extraction/analysis/memo task totals, reserved/estimated/known cost and unknown outcomes. No invoice ingestion, rate-card updater daemon, dashboards, account tiers or payment infrastructure.

### 2.5 Local artifacts and cache

- Use ignored `.local/artifacts/<mode>/` with generated internal identifiers and a configured size ceiling. No arbitrary user-supplied paths or filenames.
- Enforce path containment, reject symlink escapes, and use atomic writes. Reject unauthorized full-text retention/export based on source policy.
- Small passages/structured results remain in PostgreSQL; do not copy every payload into a file.
- Store only permitted content plus hash/reference. Metadata-only sources cannot acquire a full snapshot through cache.
- Reuse successful operation outputs using exact content/input/task/prompt/schema/model and permission/mode identity with expiry. Expired permission/changed inputs invalidate a hit.
- Search responses may coalesce within a run. New live sourcing/analysis runs in Step 3+ must perform an external search; opening saved output is separate.
- No S3, signed URLs, object lifecycle service, backup platform, large artifact catalog or background cleanup.

### 2.6 Step 2 tests and handoff

Test continuously, using a fake clock and deterministic fixture/fake providers. Fake usage can exercise admission without any real credentials or paid call.

Required integration checks:

- Migration from empty database; normal restart preserves data; round-trip typed records and missing reasons.
- Transaction rollback on invalid bundle; demo/live isolation; preserved saved references.
- Duplicate runner attempts are rejected; lock release on termination; loss of connection blocks new operations.
- Exact cache hit/miss; expiry, permission, content and version changes; no cached-only “fresh” result.
- Equality/over-limit budget boundaries, zero defaults, output cap, strong-call cap, elapsed deadline and daily ceiling.
- Crash/interrupt after reserve and before final result retains unknown liability; no automatic retry/resume; duplicate result cannot reconcile twice.
- Duplicate operation key with changed request rejected; same committed request does not call provider twice.
- Safe local paths, symlink escapes, file size limit, retention flags and atomic-write behavior.
- `.env` credentials do not enable live execution. No background tasks begin on import/startup.

Publish exact unit/integration test results and local commands. Do not silently skip unavailable PostgreSQL tests or claim fixtures prove live-provider safety. Step 2 completes only when its local integration checks pass or an explicit blocker is reported for review.

## 4. Explicitly not in Step 2

No live search/model calls or adapters; no full research pipeline; no new financial formula engine; no DCF; no memo generation; no source crawler/browser; no product UI; no FastAPI server solely for a health endpoint; no multi-user auth; no distributed queue/worker/lease/heartbeat; no automatic recovery/retry or scheduled refresh; no relationship/correction history subsystem; no cloud storage; no public deployment; no remote push.

Model routing is configuration validation and selecting an injected test adapter only. Operational cost tracking is a small safety ledger, not a billing product. Financial functionality is promoted to Step 4, not smuggled into Step 2.

## 5. Step 2 acceptance and deliverables

The operator can start local PostgreSQL, migrate, persist/read the existing demo evidence, explicitly run fixture-backed operations under hard limits, inspect retained results after stopping/restarting, and observe a graceful partial result when a cap/failure occurs. A second runner cannot spend concurrently. Live execution remains disabled. All Step 1 tests remain passing and new local database tests demonstrate the promised behavior.

Likely files: `docker-compose.yml`, backend migration configuration and migrations, small `storage/`, `runtime/` and `budget/` modules, local settings/operation contracts, fixture harness entry point, integration tests and README additions. Names are proposals, not files created in this turn.

## 6. Demo milestones

| Milestone | First available result | User-visible web demo |
|---|---|---|
| Offline visible demo | Step 2 offers a terminal fixture/persistence walkthrough; Steps 4–5 add inspectable financial/memo artifacts | Step 7 provides the first integrated visual demo for both cases |
| Live company research | Step 3 returns a fresh evidence dossier through the backend/CLI, after explicit live configuration and budget approval | Step 7 exposes the journey in the focused UI |
| Financial modeling | Step 4 gives deterministic metrics, sizing, eligible valuation and sensitivities through tests/CLI/structured outputs | Step 7 provides editable assumptions and visual results |
| Fresh sourcing → selected research → memo | Step 6 connects the completed backend flow, with Step 5 memos | Step 7 provides the complete polished end-to-end journey |

These are capability milestones, not calendar estimates. Following the requested sequence means the polished browser experience comes last. Do not call a fixture test a completed visual product. Bringing UI earlier would be a separate sequencing decision, not an unapproved implementation change.

## 7. Approval boundary

Approve SPEC.md v2 and this plan before implementation. No Step 2 services, dependencies, schemas, migrations or runtime modules have been created. All Step 1 source/tests/fixtures remain unchanged after their approval commit.
