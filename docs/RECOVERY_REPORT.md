# Recovery checkpoint — 2026-09-27

Status: recovery complete; browser demo incomplete. Stop here pending the next instruction.
This records partial implementation, not production or live-provider acceptance.

## A. Work already present at interruption

- Branch `main`, last commit `c6c61bc` (approved Step 1). Existing contracts, tests,
  fixtures, CI and calculation contracts were unchanged from that commit.
- Uncommitted README/SPEC revisions, the old Step 2 plan and archived v1 specification.
  The archive's SHA-256 matches the version in the Step 1 commit:
  `15cbb7a6adb71a864e448aeb907c938e3e4c5aa63d17b89cc7387ca636e0c8f5`.
- Six untracked partial backend files in `backend/src/vc_research/demo/`:
  `__init__.py`, `config.py`, `models.py`, `live.py`, `finance.py`, `pipeline.py`.
- Implemented code: fixed Tavily/OpenAI endpoints; explicit configuration gate;
  three-search/two-model-call caps; request/output size limits and estimated-cost
  admission; no retries; structured extraction/analysis schemas; exact quotation and
  citation-ID checks; Step 1 evidence records; nine VC sections, qualitative scenarios,
  founder questions and Markdown memo assembly.
- Financial functions: Decimal revenue growth, gross margin, runway, observed EV/revenue
  and explicit analyst-assumed revenue-multiple sensitivities. Requires reviewed inputs;
  rejects certain currency/period conflicts. Missing data and DCF have refusal paths.
- FastAPI, Uvicorn and HTTPX installed locally. No server, routes, UI, runnable demo
  provider, full-flow acceptance tests or source-backed live run had been completed.

## B. Recovery work completed

Inspected Git status, tracked diff, every partial backend module, dependency state and
Step 1 integrity before editing. Preserved the six files and all Step 1 source/tests.

- Declared HTTPX and its pinned dependencies so the partial backend and its tests are
  reproducible rather than depending on an accidental local install. FastAPI/Uvicorn
  remain unused local installations; declare them when the server is actually added.
- Fixed the financial result message when missing inputs or zero denominators prevent
  every calculation; it now explicitly says no calculation was performed.
- Added 15 focused offline test cases covering the partial pipeline, lineage, missing
  data, exact-quote rejection, identity mismatch, invalid citations, live admission,
  bounded calls/no retry, fresh search invocation, financial review, numerical results,
  scenario assumptions and incompatible inputs.
- Updated status documentation and marked the infrastructure-first sequence superseded.
  No browser/server milestone, sourcing, database, deployment or additional infrastructure
  was started. No paid requests, secrets, commits or pushes were made during recovery.

## C. Git and safety

Working tree intentionally remains uncommitted on `main`. Modified: README.md, SPEC.md,
backend/pyproject.toml and backend/requirements-dev.lock. Untracked: the six demo modules,
backend/tests/test_demo_recovery.py, docs/STEP2_PLAN.md, docs/RECOVERY_REPORT.md and
original docs/archive/SPEC-v1-approved.md. No files were deleted or reverted.

`git diff --check` passes. Existing Step 1 domain/provider/calculation files, tests and
fixtures remain untouched. Local imports do not start services or call providers.
Configuration readiness check returned live disabled, OpenAI key absent and Tavily key
absent; only presence flags were printed, never credential values. This is a safe offline
checkpoint, not certification that the partial adapters are ready for real use.

## D. Verification

One full suite after the recovery code changes:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests
```

**94 passed in 0.29s**, no failures or skips: 79 original tests plus 15 recovery tests.
The autouse socket guard blocks external network access. The test-local fake provider
is synthetic; it does not validate actual Tavily/OpenAI responses or research quality.

`python -m pip check`: **No broken requirements found**.
`git diff --check`: passed. No browser or paid-provider tests were run; no server exists.

## E. Incomplete functionality and limits

- No browser URL or launch command exists yet. No API routes, financial-review UI,
  explicit per-run confirmation handler or single-run concurrency guard.
- Live adapters are implemented but unverified against the providers. Error handling for
  unexpected provider payload shapes and interrupted runs needs integration validation.
  Cost figures are estimates, not provider invoice guarantees; socket timeouts are not a
  strict wall-clock cancellation mechanism. No cross-run spend ledger is implemented.
- `run_analysis` is a low-level injectable function, not a safe public execution boundary.
  The future server must bind mode/provider choice and live confirmation, and must not
  accept a client-supplied evidence graph as trusted financial input.
- Financial candidates require analyst review of meaning, unit/scale and comparable
  periods. Current parsing deliberately requires explicit ISO currencies and literal
  scale words, so many real disclosures will be rejected. Review is not yet accessible.
- Conflict detection only catches differing financial values for identical metric,
  currency and period strings. It is not general contradiction detection.
- Citation existence and quoted text are checked, but semantic entailment, identity,
  source independence and truth are not guaranteed. Company identity matching is strict
  and can reject aliases/redirects. Search excerpts may omit important evidence.
- No normalized comparable-company dataset, qualified DCF execution or forecast builder.
  DCF always abstains currently; illustrative multiples are assumptions, not comps.
- The result/memo are assembled dictionaries, not fully integrated ResearchRun/MemoVersion
  records. Markdown has citation labels and source URLs, but no browser rendering exists.
- No real company has completed the workflow. Fresh invocation is only tested with mocks;
  fresh API queries do not imply every underlying page was recrawled that day.

## F. Minimum remaining path to DEMO READY — not started

**Two implementation/acceptance milestones, without infrastructure prerequisites:**

1. **Connect the browser vertical slice.** One local FastAPI process, static HTML/JS,
   company input and Analyze action. Reuse the current pipeline. Wire explicit live
   opt-in, one-run-at-a-time admission, bounded/sanitized failures, in-memory report,
   evidence/source display, nine sections, qualitative scenarios, founder questions,
   financial candidate review/calculation, abstention and memo download. Bind financial
   selections to the server-held run. Add only the necessary full-flow offline fixture
   and route tests. Update dependencies, .env example and launch instructions.
2. **Verify and close the real-data path.** Configure Tavily/OpenAI keys locally and
   explicitly enable one bounded live run. Exercise a real company through the browser,
   inspect evidence and financial abstention/results, fix only demonstrated integration
   defects, and report actual calls/tokens and limitations. Verify one rich synthetic
   financial example separately and clearly label it. This milestone is blocked until
   local credentials and live-run authorization are available.

Planned local URL: `http://127.0.0.1:8000` — **not running or available at this checkpoint**.
These are two focused milestones, not two roadmap phases; the first integrates already
written code. DCF/comps beyond the supported/refusal path, sourcing, PostgreSQL,
monitoring and deployment are not prerequisites and must not expand this work.
