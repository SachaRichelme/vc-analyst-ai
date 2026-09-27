# VC Analyst AI

A local research copilot for venture capital analysts. Investment judgment stays with the analyst.

**Browser implementation is complete; real-provider acceptance is pending local credentials.**
The app supports company research, source-linked analysis, financial input review, deterministic
calculations, explicit valuation abstention and a Markdown investment memo. Offline fixtures are
clearly labeled and never used as a fallback for live research.

**Discover Startups is now the second entry point.** Define a mandate, inspect an
evidence-backed shortlist, then select a company for the existing analysis workflow.
Offline sourcing and browser handoff are tested; live sourcing is prepared but not paid-provider
validated. See [SOURCING.md](docs/SOURCING.md) for filters, usage limits and test results.

## Launch from VS Code

Open this folder in VS Code and use its integrated terminal:

```sh
.venv/bin/python -m uvicorn vc_research.webapp:app --app-dir backend/src --host 127.0.0.1 --port 8000 --no-access-log
```

Open **http://127.0.0.1:8000**. Stop the server with **Ctrl+C**. If this sprint's server
is already running, open that URL without launching a second copy. Use one process;
no `--workers`, `--reload`, public host, Docker, Node build or database is needed.

For a fresh checkout, install Python 3.12 or newer and run once:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.lock
```

Select `.venv/bin/python` as your VS Code interpreter. The existing local environment
is already installed. No installation is needed merely to launch this checkout.

## Offline walkthrough

Leave **Offline · synthetic fixture** selected, enter **Lumen**, and click **Analyze company**.
All company information and sources in this mode are synthetic. It makes zero provider calls.

Open **Financials**, review the evidence, then select:

| Input | Evidence |
|---|---|
| Prior revenue | C4 — USD 2 million, FY2024 |
| Current revenue | C5 — USD 3 million, FY2025 |
| Gross profit | C6 — USD 2.4 million, FY2025 |
| Cash | C7 — USD 1.2 million |
| Monthly net burn | C8 — USD 100 thousand |

Confirm comparability and click **Calculate reviewed inputs**: growth 50%, gross margin
80%, runway 12 months. Optional bear/base/bull multiples of 2/3/4 produce illustrative
enterprise values of USD 6/9/12 million. These multiples are explicit assumptions, not comps.
Calculations and source lineage appear in the memo. Download it with **Download memo (.md)**.

Use **Lumen Sparse** to see missing-data and valuation abstention. Other company names are
rejected in offline mode rather than silently mapped to fixtures.

## Enable live research

1. Obtain keys from [OpenAI](https://platform.openai.com/api-keys) and
   [Tavily](https://app.tavily.com/). OpenAI API billing is separate from a ChatGPT subscription.
2. Open the root `.env` locally in VS Code. This checkout already has an empty file;
   on a fresh checkout copy `.env.example` to `.env` first. Never paste keys into chat.
3. Save these variables with your actual keys:

```dotenv
VC_ENABLE_LIVE=true
OPENAI_API_KEY=your_local_openai_key
TAVILY_API_KEY=your_local_tavily_key
```

`.env` is Git-ignored. Settings are read on each run, so no restart is needed after saving
keys. Shell environment values override the file. Set `VC_ENABLE_LIVE=false` to disable live
execution again. The UI never exposes the keys.

Choose **Live · fresh public research**, enter an exact official company URL, check the
per-run authorization box, then click **Analyze company**. Loading a page, changing modes
or reviewing financial inputs never triggers paid research.

## What a live run does

- Three fresh Tavily basic searches: company/product/team; funding/traction; competition/risks.
- At most nine deduplicated source excerpts, bounded to 3,500 characters each.
- One OpenAI extraction call and one analysis call using `gpt-4.1-mini-2025-04-14`.
- Exact-quote and citation-ID checks; Step 1 evidence and missing-data contracts.
- Nine VC sections, qualitative bull/base/bear hypotheses, founder questions and memo.
- Financial candidates require analyst review before Python Decimal calculations.
  Recalculation and exports make no API calls. Missing data is never filled with zero.

No retries, loops, background activity, batch research or automatic company sourcing.
Hard call/output/input caps and an estimated USD 0.20 admission ceiling apply per run.
The time budget is checked between operations/response chunks with bounded HTTP timeouts;
it is not a strict wall-clock process-kill guarantee. An in-flight request can be billed even
if you close the tab or interrupt the server. Only one run at a time per server process.

## Limits you should present honestly

This is a bounded public-information research draft, not complete diligence. Search results
can be stale even when the API query is fresh; retrieval and publication dates are separate.
Quotation checks do not prove truth, source independence or semantic support for an inference.
The analyst must review identity, citations, contradictory evidence and financial definitions.

Financial extraction is deliberately strict about explicit currency and scale. Many real
companies will produce abstention. Revenue growth, gross margin, runway and observed EV/revenue
are supported when reviewed inputs permit. Assumed revenue-multiple sensitivities are supported;
normalized peer valuation and DCF execution are not. DCF always displays the missing-input reason.

Only the last successful report is held in memory. Restarting the server loses it; download
memos you want to keep. A failed new run does not replace the last successful report. No database,
accounts, cloud deployment or monitoring is included. Sourcing runs only on an explicit user
request and never automatically analyzes its candidates. Do not expose this local app online.

## Tests

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests
.venv/bin/python -m pip check
```

Tests block outbound sockets and make no paid calls. All 94 tests at the recovery checkpoint
remain; route tests exercise browser assets, reports, finance, export, admission and isolation.
One Starlette warning concerns its future TestClient transport migration; it does not affect
production HTTPX calls or the currently pinned passing tests.

An optional real-browser harness is in `tools/demo-browser-smoke.cjs` (requires Playwright
and installed Chrome). With the server running, `node tools/demo-browser-smoke.cjs` tests
only offline data. `PLAYWRIGHT_MODULE` can point to an existing Playwright installation.
The explicit `--live` option makes ONE real run and must only be used intentionally after
configuring credentials. It saves acceptance receipts to ignored `.local/`; it never retries.

## Code and project history

- `backend/src/vc_research/domain/`, `providers/`, `calculations.py`: preserved Step 1 foundations.
- `backend/src/vc_research/demo/`: bounded providers, extraction/analysis, Python finance, fixtures and static UI.
- `backend/src/vc_research/webapp.py`: minimal FastAPI application and single-process admission.
- `backend/src/vc_research/sourcing/`: bounded discovery, evidence validation, mandate filtering and synthetic sourcing fixtures.
- `backend/tests/`: contract, recovery and route tests.
- `docs/DEMO_GUIDE.md`: costs, demo script and validation status.
- `docs/RECOVERY_REPORT.md`: historical checkpoint before browser integration.
- `SPEC.md`: historical broader scope, superseded in sequencing by demo-first instructions.
- `platform/`: preserved inactive earlier scaffold; not used to run this app.

Sourcing is implemented; infrastructure expansion remains deferred. Nothing is deployed or pushed.
