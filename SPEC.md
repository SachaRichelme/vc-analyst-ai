# VC Research Copilot — Portfolio Demo MVP

> Demo sprint, 2026-09-27: the latest user instructions supersede the sequence below.
> The local company-analysis browser vertical slice is implemented and tested offline.
> Sourcing is now implemented as an explicitly requested second mode; see [SOURCING.md](docs/SOURCING.md).
> Real-provider acceptance remains unverified; infrastructure expansion remains deferred.
> See [README.md](README.md) and [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for current operation and validation status.

Version: 2.0 — scope revision proposed for approval
Date: 2026-09-26
Implementation status: Step 1 approved and committed; Step 2 NOT authorized yet.

This is the revised product specification. It replaces the v1 scope and sequence while preserving its evidence, missing-data and cost-safety principles. [The exact previously approved v1 specification](docs/archive/SPEC-v1-approved.md) is retained as historical design material, not a competing implementation plan. The latest user instructions govern this revision.

## 1. Product decision

Build a technically credible, cost-efficient **portfolio/demo project for VC recruiting**, also useful to its single operator for occasional real sourcing, research, financial analysis and memo preparation.

The six visible pillars are: fresh startup sourcing; evidence-backed company research; deterministic financial modeling and valuation; high-quality VC analysis; investment memos; and a focused demo interface. Investment judgment remains human. No automated INVEST/PASS decision or investment score.

The primary journey is **discover → select → analyze → financial modeling where supported → diligence questions → memo**. A user may enter a company name or URL directly. Names must resolve to a confirmed identity before research. Stored knowledge and cache supplement fresh external research; they never define the boundary of the research universe.

This is not a multi-user SaaS, continuously running intelligence platform, CRM, portfolio monitor or production-scale database. Persist enough to make research inspectable, avoid duplicate calls, and reopen recent analyses. Build less operational infrastructure and invest the effort in analytical quality.

Quality priorities remain evidence reliability, analyst usefulness, research quality, cost safety, reproducibility, speed, then feature count. A polished demo must never obscure unknowns or turn synthetic financials into claims about a real company.

### Analytical scope

The first specialist templates cover (A) Seed–Series A B2B software and (B) a more mature private/growth software company with sufficient financial inputs. Geography starts with Europe/UK/US and English-language sources. Sourcing can identify other businesses, including ClimateTech, but specialist analysis must declare its limitations rather than apply SaaS economics indiscriminately.

Financial modeling is a core MVP pillar, not a distant future feature. The implementation sequence within Step 4 is incremental: metrics, sizing, method eligibility, multiples/scenarios, then DCF/sensitivity with qualified inputs. The deliverable includes an honest refusal path as well as successful models. Do not require a private real company to disclose information merely to make the demo work: the rich financial offline case may use labeled synthetic, permitted or analyst-entered assumed inputs.

## 2. Scope contract

| MVP — BUILD IN STEPS 2–7 | LATER / FUTURE | DO NOT BUILD |
|---|---|---|
| Fresh external sourcing plus saved company candidates | Multi-user/team features if ever justified | Automated investment decisions or arbitrary fit/confidence percentages |
| User selection before substantive company research | Continuous/scheduled monitoring, portfolio intelligence, CRM | Automatic deep research of all sourced companies |
| Fresh company research, dated evidence and explicit unknowns | Sophisticated history timelines and relationship/correction tracking | Investor personalities, IC voting, autonomous agent hierarchies |
| Lightweight PostgreSQL persistence, recent reuse/cache | Distributed workers, leases, heartbeats, automated recovery/resume | Kubernetes, Kafka, Redis, microservices for this demo |
| Simple bounded local execution and operation usage records | Full billing/reconciliation infrastructure | Paid provider replicas or access-control bypasses |
| Deterministic metrics, market sizing, appropriate valuation | Additional specialist sector templates and data adapters | Graph/vector databases without demonstrated need |
| Thesis dependencies, Why Now, targeted skeptical validation | Advanced comparable data feeds and proprietary databases | Fabricated financial inputs or automatic DCF for sparse startups |
| Memo with citations and financial/valuation sections where supported | Private document ingestion, professional PDF, editable spreadsheet export | Broad cloud/production artifact infrastructure |
| Focused UI with evidence, assumptions, progress and errors | Theme discovery, Find Similar Companies, Fund Intelligence | A large SaaS dashboard |
| Two labeled offline demo narratives; occasional opt-in live research | Advanced historical refresh/diff and cross-company knowledge automation | Scheduled or background paid activity |

Source snapshots and frozen memo input manifests remain MVP because they make citations reproducible. They do not require a comprehensive bitemporal company knowledge system. Keep existing future-facing contracts and tests without implementing their whole lifecycle.

## A. Final MVP architecture

React/TypeScript/Vite → FastAPI (when API delivery is needed) → ordinary Python application services → PostgreSQL → controlled provider adapters. One local operator, one explicitly launched run at a time. A CLI/test harness precedes the product UI.

| Component | Decision |
|---|---|
| Frontend | Focused React/Vite views at Step 7; no SSR requirement |
| Backend | Python/Pydantic; FastAPI added for the research/API interface, not for Step 2 ceremony |
| Workflow | Plain Python bounded functions: plan/extract → VC analysis → deterministic finance → skeptical validation → memo |
| Storage | PostgreSQL with SQLAlchemy/Alembic; one local database, explicit demo/live mode on records |
| Runtime | Explicitly invoked local runner; no queue worker, scheduler, polling loop or automatic restart |
| Providers | One search and one model provider first, behind existing contracts; no live adapters in Step 2 |
| Costs | Shared operation gate, persisted reservations/results, hard run limits and simple operator spend ceiling |
| Artifacts | Ignored local directory only for permitted content too large for database text or exports |
| Extraction | Controlled HTTP retrieval/HTML cleaning at Step 3; complex document ingestion deferred |
| Calculations | Versioned allowlisted Python functions with Decimal, typed input provenance and tests |

LangGraph is now a reference/future option rather than a required dependency. Nothing from it is currently implemented, so this avoids work rather than replacing working code. No distributed durable workflow engine is needed.

A local PostgreSQL advisory lock on a dedicated connection prevents simultaneous runners, including duplicate CLI/UI starts. Loss of that lock/connection halts admission of new external calls. Run/operation writes use short transactions, not one long transaction over network calls. Restart never resumes spending automatically. A stale running record is marked interrupted/partial on an explicit next invocation after establishing no other runner owns the lock; uncertain operations retain their reserved estimate. This is minimal spend safety, not general job recovery.

Services bind to loopback. No public backend deployment is in scope. Authentication/authorization would be required before internet exposure; a private frontend does not secure its backend.

## B. Minimal persistence model

Step 2 proposes nine small tables. Use UUID identity, UTC timestamps, numeric money columns, constrained states, mode-scoped foreign keys, and validated versioned JSONB payloads for contract fields that do not need database queries. This balances simple storage with real relational evidence integrity.

| Table | Purpose |
|---|---|
| `companies` | Canonical domain/name and mode, safe exact deduplication, first seen; no fuzzy automatic merges |
| `source_documents` | URL, publisher, rights and retention policy; source identity |
| `source_versions` | Document FK, content hash, dated observation metadata and optional permitted local content reference |
| `evidence_passages` | Version FK, exact excerpt and locator |
| `claims` | Company FK, typed claim payload, as-of date; never silently overwrite inputs already cited by a saved analysis |
| `claim_evidence` | Claim/passage FKs, supports/contradicts/qualifies relation and claim-specific quality reasons |
| `research_runs` | Input/config snapshot, kind/mode/status, timestamps, stop reason, budget, retained structured outputs and input manifest |
| `operations` | Run FK, unique operation key, cache key/expiry, reservation, status, usage/cost and reusable result reference |
| `memo_versions` | Company/run FKs, structured memo plus frozen claim/calculation manifest, generated/cutoff dates; append-only saved versions |

Only identity, lookups, joins, status/cost and integrity-critical fields need relational columns; remaining Step 1 Pydantic data can be stored as validated JSONB. Do not collapse sources, passages and claims into one undifferentiated memo blob.

Analysis, thesis, questions and calculation records may initially be typed run-output snapshots. The finance step adds any genuinely needed calculation query/index/schema extension when used. Cross-reference validation must still ensure saved calculation/claim manifests resolve within the correct mode; JSONB does not waive integrity checks.

No separate generic entities, relationship history, correction-event store, run-event bus, graph tables or lease table in Step 2. Existing relationship/correction contracts stay in source for future use. A future analyst edit creates an explicitly labeled revised output and retains its cited input; no elaborate correction propagation engine.

Cache lookup uses exact successful operation keys, content hashes, relevant model/prompt/schema versions, mode and rights scope. Never reuse restricted/expired content. The same URL can have multiple retained source snapshots; this is citation integrity, not a full company timeline product.

## C. Research and sourcing behavior

### Sourcing (Step 6)

Validate mandate → search stored candidates AND issue fresh external search → resolve/deduplicate → bounded retrieval/light enrichment → code filters and cheap classification only when needed → explained shortlist → save useful evidence → user selects ANALYZE.

Cards expose company, sector, stage/geography where evidenced, matched/unknown criteria, recent signal and date basis, discovery time, why surfaced, and sources. Initial signal windows are 7 days, 30 days and all history; 24/90-day controls can follow without changing semantics. Filters concern events/announcements, not the startup's founding date. Unknown dates do not satisfy a strict recency filter.

A database-only result cannot satisfy a live sourcing request. If external search fails, show partial existing results with “fresh discovery failed.” Search indexing and source access mean yesterday's startup is discoverable in principle, not guaranteed to be found. Do not promise exhaustive coverage.

### Company analysis (Steps 3–5)

Resolve company name/URL → load relevant prior evidence → perform fresh targeted external search for material developments → retrieve permitted sources → clean and extract relevant passages/claims → cross-check → VC analysis and thesis dependencies → deterministic finance and eligible valuation → targeted skeptical validation → founder questions → cited memo.

A newly requested live analysis must attempt fresh external discovery even if cached evidence exists. “Open saved analysis” is a separate zero-research action and keeps its old as-of date. Same-run query deduplication and reuse of unchanged extraction are permitted; prior-day search replay cannot be labeled a fresh pass.

Funding, launches, customers/partnerships, geography, management changes, regulation, market shifts and competitors are investigated when material. Negative searches target the weak assumptions of the thesis, not a rote list of allegations. Evidence must retain attribution and caveats.

The system returns a partial dossier on budget exhaustion, source failure or private-information gaps. Supported recent findings remain usable without a complete memo. A missing retention figure is not evidence of poor retention.

## D. Controlled analytical workflow

Use a few task roles, not separately autonomous agents. Planning and extraction may share a bounded orchestration function while keeping their input/output contracts. VC interpretation, skeptical validation and memo writing remain logical stages so they can be evaluated independently. Finance is a deterministic service, not an arithmetic agent.

Model calls occur only where semantic interpretation adds value. Code handles matching, filtering, dates, caching, hashes, sorting, transformations, arithmetic, validation, budget admission and citation rendering. Pass relevant structured claims and short excerpts to analysis rather than repeated whole webpages/dossiers.

The planner records material unanswered questions. Deterministic stopping rules decide whether an additional call has plausible value: untried credible source, important missing answer, budget remaining. No extra LLM call just to decide whether another call is worthwhile. All follow-up loops and output tokens are bounded.

## E. Evidence architecture

Visible statement classes: **FACT, COMPANY CLAIM, CALCULATED VALUE, INFERENCE, ASSUMPTION, UNKNOWN**. Separately record derivation (`reported`, `calculated`, `inferred`, `estimated`) and verification state (`unreviewed`, `supported`, `partially_supported`, `conflicted`, `unsupported`). Human review is another explicit state, not proof of factual truth.

Source quality is assessed on each claim–evidence link: relevance, authority for that proposition, directness, recency, independence and extraction ambiguity. A company website can establish what product it offers or claims to offer; it cannot independently establish market leadership. A registry supports legal identity, not product-market fit.

Require every material factual memo claim to reference an actual evidence passage. Validate that the passage exists and that the statement preserves entity, date, metric, qualifiers and attribution. An LLM support checker is fallible and supplements deterministic checks and human review.

Retain contradictions instead of averaging them away. Funding total versus round size, ARR versus revenue, and disclosed logos versus paying customers must remain separate predicates. Repeated press-release coverage counts as one origin when that dependence is known.

Coverage is qualitative: **strong, moderate, limited, unknown**, with a reason and visible conflicts. Strong means the material questions for that section have direct relevant support without unresolved material contradictions; it does not mean the company is attractive. Unknown financials cannot be offset by numerous product sources. Do not present an aggregate confidence percentage.

Store thesis dependencies as evidence-linked propositions. Each has supported/partial/limited/unknown/conflicted status, strengthening and weakening conditions, and the next evidence needed. Unsupported allegations from complaints or negative searches must not become established facts; material allegations retain attribution, source limitations and any relevant response.

## F. Missing-data architecture

Use typed nullable values plus explicit reasons, never zero, an empty string or invented estimates to fill missing financials.

| Reason | Meaning / display |
|---|---|
| `not_searched` | Not investigated in this scope |
| `not_found_in_reviewed_sources` | “Not publicly available in the sources reviewed as of [date]” after a completed bounded search |
| `access_restricted` | Relevant source was inaccessible or unauthorized |
| `budget_exhausted` | Research incomplete because a configured limit was reached |
| `provider_failure` | Research incomplete because a dependency failed |
| `conflicting_evidence` | Reliable resolution is unavailable; show alternatives |
| `not_applicable` | Metric/question does not apply to this business model |
| `requires_private_information` | Likely requires founder/authorized private evidence; not a claim of proven universal nondisclosure |
| `stale_only` | Only historical evidence is available for a current-state question |

Record search attempts and scope on the question. A sparse memo can be a valid result if limitations are explicit and founder questions are useful. Lack of public retention data is not evidence of poor retention. A budget-limited search cannot assert the information does not exist.

## G. Simple cost-control architecture

Keep hard limits on search requests, documents/bytes, follow-up rounds, LLM calls, strong-model calls, tokens, estimated spend and elapsed time. Default live execution remains disabled. Credentials never imply permission to spend.

One central operation gate is mandatory before paid adapters are introduced. For each potentially billable attempt: check mode/config and eligible cache → estimate a conservative reservation → persist it and verify run plus simple operator spend ceiling transactionally → make one bounded call → record usage/outcome. Retries need their own reservation; default to no automatic retry for ambiguous billed failures. Unpriced operations fail closed. Bound provider output and timeout before dispatch.

One-run-at-a-time admission removes the need for a distributed billing architecture but does not justify in-memory-only spend counters. Persist counters/operation rows so a restart cannot silently reset allowance. A single UTC daily ceiling is sufficient initially; retain the existing monthly-limit field but do not build a monthly billing subsystem. Any nonzero configured monthly ceiling must either be enforced by a simple ledger sum or explicitly rejected as unsupported—never silently ignored.

On unknown timeout/billing outcome retain the conservative reservation; operator inspection is required before retry. Do not claim exactly-once external calls. Cancel stops new calls; in-flight provider charges may still apply. Exhaustion saves useful work and gives a clear partial-result reason. Rendering existing results is deterministic and does not require a final model call.

This is application admission against estimates, not an exact invoice guarantee. Keep provider-side spend controls where available and no automatic top-ups. Rate-card version and estimated versus reported usage/cost remain visible. No subscription billing, payment system, distributed quota service, background invoice reconciliation or production cost dashboard.

## H. Model-routing architecture

Maintain configuration by task: provider, model ID/revision where exposed, capability requirements, tier, prompt/schema version, context/output limits, timeout, and allowed fallback.

| Task | Initial route |
|---|---|
| Discovery, filtering, dates, matching, calculations, rendering | Code/search; no LLM unless ambiguity genuinely requires it |
| Ambiguous classification | Cheap tier |
| Evidence extraction | Cheap tier if evaluation passes; medium otherwise |
| Planning | Medium tier |
| VC interpretation | Strong tier with bounded calls |
| Skeptical review | Medium initially; strong only for measured quality improvement |
| Memo synthesis | Medium initially |

Do not silently escalate to a more expensive model. Every escalation needs an allowed route and a new budget reservation. At most one configured repair/escalation for an invalid structured output before returning an explicit failure/abstention. Model outages may use an approved fallback within budget or yield partial results; never silently substitute demo outputs.

Benchmark task-specific support precision and abstention against cost. Exact model names and monetary profile prices are implementation configuration, not architecture. Record returned model revision where available; mutable aliases limit reproducibility and must be disclosed.

## I. Freshness and lightweight reuse

Fresh external search is mandatory for each newly requested live sourcing or company-analysis run. Cache supplements it; an explicit open-saved-analysis action does not perform research. No scheduled refresh, background polling or automatic monitoring.

Keep publication, observation, retrieval, discovery and verification timestamps distinct. Re-fetching a 2023 revenue statement today does not make its revenue current. Historical funding events remain historical; “latest funding” needs a fresh completeness check. Unknown dates remain unknown.

Within a run, deduplicate queries and source URLs. Across recent runs, reuse permitted unchanged source extraction keyed by content hash + extractor/task/prompt/schema/model revision + context when company-conditioned + mode/rights scope. Use exact matches initially. Reuse analysis only when its exact relevant evidence/assumption/config manifest is unchanged and it is displayed with its actual as-of date.

Step 2 supplies a simple expiry and successful-result lookup. Source-specific TTL policy and conditional retrieval are added with actual adapters in Step 3. The elaborate v1 freshness/decay machinery, dependency invalidation graph and historical “what changed?” UI are deferred. Preserve prior saved memos and evidence snapshots; no automatic deletion/replacement of cited inputs.

## J. Two-case demo strategy

Demo mode uses the same domain/provider contracts but no external network or credentials. Every screen/export says DEMO, identifies synthetic or permitted fixture data, and shows evidence dates. Unsupported demo inputs abstain. Live failures never switch silently to demo. Demo/live persistence and cache entries are separated by mode.

| Narrative | Demonstrate |
|---|---|
| A: Early-stage startup | Fresh-discovery replay; fragmented evidence; team/product/market/competition/Why Now; funding/traction; unknown retention, burn and ARR; useful founder questions; explicit financial/DCF refusal |
| B: Mature private/growth company | Richer evidence or clearly labeled synthetic/analyst assumptions; growth/retention/margin/burn metrics; comparable rationale; valuation scenarios; qualified DCF and sensitivity; evidence-linked financial interpretation |

Keep all four Step 1 development fixtures unchanged as regression tests. Add the two richer narrative bundles when their analytical steps are built. Case B must not silently reuse invented values as facts about a real company. Analyst-entered assumptions are typed/labeled, not private-document ingestion. No live access is necessary to show the offline financial model.

## K. Evaluation strategy

Continuous offline tests remain mandatory. Keep synthetic development fixtures and add gold-standard numerical examples, financial missing-input/refusal cases, unit/period mismatches, valuation eligibility cases and sensitivity checks. Manually review claim support and founder-question usefulness on a small disclosed real/permitted evaluation set as live research becomes available.

Compare a simple one-pass baseline using the same sources/scope. Measure citation coverage separately from support precision; qualification precision within a defined search universe; conflicts/abstention; analyst edits; latency; and cost per sourcing, analysis, memo and fresh rerun. Compare cheap/strong task models only through opt-in bounded evaluations. No claimed per-run price or professional accuracy without measurements.

The previously suggested 20–30 cases remains a growth target, not a reason to delay a visible prototype. Publish case counts, provenance and limitations. The target of at least 95% human-supported sampled material claims remains a quality target, not a claim that the current 79 structural tests demonstrate it.

## L. Revised implementation sequence

1. **Contracts and fixtures — complete:** retain approved Step 1 and its tests.
2. **Minimal Runtime and Persistence:** minimal local PostgreSQL, run/operation storage, sequential explicit runner, hard cost limits, safe config, fixture-backed execution, minimal artifact/cache handling. Exact plan: [STEP2_PLAN.md](docs/STEP2_PLAN.md). Stop for review.
3. **Live Research and Evidence:** one fresh search provider, safe retrieval/cleaning, passage/claim extraction, identity resolution, targeted/disconfirming research, validated dossier/backend representation. Opt-in live credentials and budgets required.
4. **VC Analysis + Financial Modeling:** company/market/competition/Why Now/risks/questions; deterministic metrics; market sizing; method eligibility; comps/scenarios; DCF/sensitivities when supported. Deliver in tested sub-slices, not one giant financial module.
5. **Investment Memo:** cited memo, financial/valuation sections, explicit unknowns, skeptical validation and Markdown export.
6. **Fresh Startup Sourcing:** mandate, fresh discovery, deduplication, lightweight qualification, Why This Surfaced, company selection; card-ready data.
7. **Demo UI:** focused React/Vite sourcing, analysis, evidence, financial assumptions/results, valuation, memo and progress/error views. No large SaaS shell.

Tests accompany every component; each step ends with a reviewable result. No calendar estimates are implied. Backend/CLI milestones precede the polished interface; do not claim a terminal result is the completed visual demo.

## M. Testing strategy

Preserve the offline unit/contract suite. Add local PostgreSQL integration tests in Step 2 with dedicated test configuration; do not substitute SQLite for database behavior. An explicitly requested integration suite fails clearly when PostgreSQL is absent rather than silently passing/skipping. No paid endpoints in default tests.

Step 2 tests persistence/restart visibility, mode isolation, reference integrity, exact deduplication, cache permissions, single-run lock, durable reservations, cap boundaries, idempotency keys, interrupted/unknown operations, cancellation and safe local artifact paths. Recovery means reporting retained partial state, not auto-resuming jobs.

Later tests cover source date meaning, unsupported/contradictory claims, SSRF/redirect/IP checks, untrusted content, deterministic formulas, incomparable metrics, missing inputs, valuation refusal, DCF sensitivities, citations and offline UI journeys. Live benchmarks stay opt-in and budgeted. Dependency installation may access registries; research tests do not call live providers.

## N. External dependencies

Local PostgreSQL; Python/Pydantic with SQLAlchemy/Alembic and a PostgreSQL driver at Step 2; one search provider and one model provider at Step 3; FastAPI for local API delivery; React/Vite at Step 7. No live network adapter or model/search SDK is necessary in Step 2. No LangGraph, Redis or cloud storage dependency by default.

Public/free sources and documented APIs remain preferred. Company/investor websites and funding announcements support attribution; public registries support relevant legal/filing facts. Media, accelerator directories and job signals require access checks and precise interpretations. Proprietary startup databases are optional later adapters, never prerequisites. Retention/model-processing/export rights must be checked independently.

## O. Free/local operation

The local app, PostgreSQL, fixtures, calculations and export rendering can run without paid services. Search free allowances may support small experiments but are not assumed unlimited or permanent. LLM inference and some live search/data services may cost money. Hosting is not required for the interview demo.

## P. Potentially billable actions

Fresh search, uncached extraction/classification, planning, analysis, skeptical review and changed memo synthesis may incur cost, including potentially billed failed/retried attempts. Opening saved results, deterministic financial calculations, inspecting assumptions/evidence, and rendering existing exports require no LLM. Changing assumptions reruns code; interpretation regeneration is a separate explicit action.

## Q. Cost measurement

Record task, provider/model/version, run/company, operation/attempt, cache hit, request limits, tokens/search requests/documents, rate-card version, reserved/estimated/reported cost, latency/time and outcome. A basic per-run breakdown is enough. Unreported usage/cost must not silently mean zero. Avoid charging the same shared sourcing work to every company. All caps apply before dispatch; no research may continue spending after a cap.

## R. Portfolio Demo MVP acceptance criteria

1. The unchanged Step 1 contract suite remains passing; later changes preserve fixtures or introduce explicit version migration tests.
2. Step 2 survives a normal stop/restart with inspectable saved cases and operation costs. Duplicate runners are rejected. Interrupted work never resumes paid activity automatically.
3. Every new live sourcing and company-analysis run attempts fresh external discovery. Cached-only fallback is explicitly partial. A test surfaces a previously unseen company.
4. Sourcing remains lightweight; no substantive research without user selection. Cards explain matches/unknowns, evidence, event date basis and why surfaced.
5. Material factual memo claims resolve to evidence and preserve attribution/qualifiers. Unknowns/conflicts are visible; independent human support precision is measured rather than inferred from passing schema tests.
6. All financial arithmetic uses tested code with typed units, periods, definitions and lineage. Missing or incompatible inputs yield a reason and blocked analyses, not invented values.
7. Case A refuses an unsupported DCF. Case B demonstrates deterministic metrics, at least one justified multiple/scenario model, and DCF plus sensitivities using explicitly eligible inputs. Comparable choices expose similarities and limitations.
8. Market sizing separates reported estimates and calculated assumptions, uses a defined customer universe and time/geographic scope, and never fills SOM with an arbitrary percentage.
9. Budget/time/token/call limits, daily guard, ambiguous-charge behavior and disabled-live defaults pass offline tests. No invoice precision or cost claims without evidence.
10. Both narrative demos run offline without keys and remain labeled. Live failure does not substitute fixture data. The final UI makes sources, assumptions, missing information and failures easy to inspect.
11. Saved memos retain an as-of date, evidence cutoff and input manifest. Where retention prevents exact reproduction, disclose it.
12. Normal local VS Code setup/run/test/stop commands are documented. No public deployment, monitoring service or remote push without separate authorization.

## S. Financial modeling and valuation — core MVP

### Deterministic metric families (Step 4)

Implement small versioned pure functions with Decimal and golden/edge-case tests. Start with revenue/ARR growth, CAGR, gross margin, net burn, runway, burn multiple and Rule of 40; then cohort/retention and acquisition efficiency as explicit definitions permit: NRR, GRR, churn, CAC, LTV, CAC payback and sales efficiency. Add revenue/ARR multiples and EBITDA multiples only when meaningful. Do not generalize SaaS definitions to every business.

Each metric records required inputs, definitions, unit/currency, period/cohort/entity, formula version, assumptions, output precision and provenance. Inputs come from cited claims or explicitly analyst-entered assumptions, never hidden model completion. The LLM may propose a metric and interpret results; code controls eligibility/arithmetic.

A positive prior revenue is required for ordinary growth; CAGR needs valid endpoints/horizon; runway needs unrestricted cash and a defined burn assumption, not cumulative funding; retention needs a consistent starting cohort; CAC/LTV need aligned acquisition/gross-margin/churn definitions; Rule of 40 names its profitability measure. Invalid denominators, incomparable periods or absent inputs return explanatory unavailability. Missing data also identifies which analyses are blocked and suitable founder questions.

### Valuation eligibility and methods

Use deterministic prerequisites plus analyst-reviewed methodological reasoning. Output each method as eligible, conditional on explicit assumptions, or unavailable, with reasons and missing inputs. Maturity alone never unlocks a method.

- **Public comps:** economic similarity in customers, revenue model, growth, margins, scale and capital intensity; explain exclusions/differences. Use credible dated data and distinguish EV/equity, historical/forward periods and gross/net revenue. A small manually curated permitted/synthetic demo set is sufficient; a paid market-data universe is not required.
- **Transactions/funding comps:** use only reliable terms; disclose instrument, rights, date and context. A funding round is not automatically a comparable enterprise value.
- **Multiples:** show selected range, source/assumption, normalization and EV-to-equity bridge where supported. Do not invent debt/cash or an arbitrary private-company discount.
- **Scenario/venture returns:** explicit entry/exit basis, dilution, ownership and time horizon. Do not imply common-stock returns capture preferences or instruments not modeled.
- **DCF:** requires a credible or explicitly hypothetical forecast, consistent unlevered cash flows/discounting, terminal assumption and equity bridge if equity value is shown. Unsupported forecasts do not become facts. Reject invalid perpetual growth/discount combinations; state discounting convention and currency.
- **Sensitivity:** deterministic recalculation over declared assumptions (e.g. growth/discount rate or metric/multiple). Show ranges and drivers, not a falsely precise target price.

### Market sizing

Support top-down published estimates and bottom-up calculations separately. Prefer bottom-up credible customer universe × annual spend/revenue per customer. SAM restricts serviceable product/geography/regulation. SOM reflects a time horizon and plausible acquisition/delivery capacity. Expose adoption/pricing/spend assumptions, evidence, formula, range, base year and limitations. No arbitrary SOM fraction.

### Memo and review

The memo includes Executive Summary, Company Overview, Team, Product, Business Model, Traction, Market, Competition, Why Now, Financial Analysis, Valuation when appropriate, Risks, Critical Unknowns, Founder Questions and Sources. Financial sections may correctly show unavailable methods. Preserve thesis dependencies, strengthening/weakening evidence and skeptical validation. No automated investment verdict.

## Source access, security and reproducibility policy

Prefer primary sources for the specific claim. Use search for discovery, documented APIs or structured data where appropriate, and limited permitted retrieval where necessary. Source accessibility, retention, model-processing rights and export permissions are separate decisions.

Store full source snapshots only where permitted. Otherwise retain allowed excerpts/metadata and record the reproducibility limitation. A content hash identifies input but cannot reconstruct deleted content. Retention/deletion rules override indefinite reproducibility; preserve audit metadata where permitted and mark source content unavailable.

Do not collect irrelevant personal/sensitive information, circumvent controls, or treat robots.txt as a complete legal authorization. Honor applicable terms, licenses, privacy requirements and source limits. Official registry data is not authoritative on commercial success. Review rights for every fixture and future paid adapter; code licensing does not license provider data.

Retrieved content is untrusted data. Tools are allowlisted and read-only except controlled persistence. The LLM cannot alter budgets, call arbitrary network endpoints, read secrets or run code. Fetchers validate protocols, public IP destinations and redirects, bound response size/time, and isolate risky document parsing when added. Logs contain bounded operational information and redacted errors, not credentials or hidden model reasoning.

Reproducibility means preserving permitted inputs, exact manifests, formula/config versions and recorded outputs. It does not promise bit-for-bit regeneration from a nondeterministic or mutable remote model.

## Repository and prior-work policy

Retain the existing repository and Step 1 package, tests, fixtures and inactive `platform/` scaffold. Add only modules needed by the current step. Step 2 will add local storage/runtime/budget modules and migrations; no queue-worker package is required. A focused `apps/web/` UI comes later without deleting the old scaffold as incidental cleanup.

Keep secrets and generated artifacts ignored; version safe examples, migrations, fixture provenance, formula definitions, tests and decision notes. [STEP1_REPORT.md](docs/STEP1_REPORT.md) and the original ADR are historical records; their future-step descriptions are superseded here. [STEP2_PLAN.md](docs/STEP2_PLAN.md) gives the current contract review and exact proposed next step.

## Research references and reuse decisions

References below come from the architecture research in this conversation on 2026-09-26. Provider availability, licenses and pricing must be rechecked when selecting implementation versions; no live service was purchased for this specification.

| Reference | Decision |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Reference only; plain Python orchestration for the demo, adoption deferred until a measured need |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | Study bounded planning/research patterns; archived repository, not the maintained application foundation |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Study search/report separation and citations; build our own claim validation |
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | Study typed task/evaluation interfaces; do not add a second orchestration framework initially |
| [Diligence](https://github.com/beastofbayarea/diligence) | Study claims/unknowns/founder questions; do not assume public-company verification generalizes to startups |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | Study provider separation; exclude investor personas and trading/decision logic |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB), [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | Study normalization/formulas for later finance work; avoid unnecessary platform dependencies |
| [Trafilatura](https://github.com/adbar/trafilatura) | Reuse HTML extraction after access checks |
| [Docling](https://github.com/docling-project/docling), [WeasyPrint](https://github.com/Kozea/WeasyPrint) | Later document extraction/PDF candidates; review selected code/model licenses |
| [Tavily](https://docs.tavily.com/documentation/api-credits), [Brave](https://brave.com/search/api/) | Evaluate one search provider first; check credits, billing and retention rights |
| [Companies House](https://developer.company-information.service.gov.uk/overview), [Sirene](https://www.insee.fr/fr/information/3591226), [SEC](https://www.sec.gov/about/developer-resources) | Optional official identity/filing adapters with source-specific limits |
| [Greenhouse](https://docs.greenhouse.io/job-board.html) | Possible later public job-signal adapter, not a headcount estimator |
| [Crunchbase](https://data.crunchbase.com/docs/welcome-to-crunchbase-data), [Dealroom](https://docs.dealroom.co/docs/premium-api), [PitchBook](https://pitchbook.com/help/PitchBook-api) | Paid extensions only after explicit access and retention/export review |
| [CNIL public-data scraping guidance](https://www.cnil.fr/fr/node/165906) | Public accessibility is not blanket permission to collect/reuse personal data |

## Revision map and approval boundary

Changed from v1: sections 1–2 (portfolio purpose/scope); A–B (runtime/storage); C–D (fresh company research and fewer roles); G (simpler costs); I (lightweight cache); J (two narratives); K (evaluation scope); L–M (sequence/tests); N–Q (dependencies/measurement); R (demo acceptance); S (finance/valuation promoted); repository policy and LangGraph reuse decision. E–F, task-aware routing in H, and source/security/reproducibility principles remain substantively intact.

This revision and Step 2 plan await user approval. No Step 2 code, migration, service provisioning or live call is authorized by this planning turn. Step 1 is preserved in its approved commit. Do not begin Step 2 until the user approves the revised scope and plan.
