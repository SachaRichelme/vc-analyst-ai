# Fresh startup sourcing

**SOURCING READY: YES for the offline browser journey and prepared live adapter.**
No paid sourcing run was made. Live provider output/research quality is not yet validated.
Company analysis, its evidence/financial/memo pipeline and Step 1 contracts remain intact.

## Try it locally

The running application is at http://127.0.0.1:8000. Refresh the page to load the new navigation.
To launch from VS Code if the server is stopped, open the repository folder and run from its root:

```sh
.venv/bin/python -m uvicorn vc_research.webapp:app --app-dir backend/src --host 127.0.0.1 --port 8000 --no-access-log
```

1. Click **Discover Startups**. Keep **Offline · synthetic sourcing** selected.
2. Select Seed, Enterprise Software / SaaS, Europe and Last 30 days. Multi-select with Cmd/Ctrl.
3. Click **Discover startups →**. Expect two synthetic candidates: a supported mandate match
   and a potential match with missing information. A duplicate is removed and an old event excluded.
4. Expand **Discovery evidence**. Review the quotation, source URL and publication/retrieval dates.
   `.example` URLs identify synthetic sources; they are not real external articles.
5. Under Funding/age/exclusions, uncheck **Keep companies with unknown funding eligible** and
   rerun: only Lumen remains. Exclude `lumen.example` and rerun: no candidates remain.
6. Remove those refinements and select a card's **Analyze company →**. This switches to the
   existing Company Analysis form and fills its identity/mode. It makes no research call.
7. Click the existing **Analyze company →** action to run the chosen synthetic analysis and memo.

Offline dates are deterministic relative to the supplied UTC run date: synthetic recent events
are three days earlier; the stale fixture is 400 days earlier. There are only two selectable
synthetic companies. This small fixture set is not advertised as market coverage.

## Live workflow and limits

Uses the existing `.env` variables: `VC_ENABLE_LIVE=true`, `OPENAI_API_KEY`, `TAVILY_API_KEY`.
Choose Live in Discover, check the per-run authorization box, then submit a mandate.
No additional provider, credentials, persistence or infrastructure is needed.

Pipeline:

`Mandate → 3 fresh Tavily basic searches → up to 30 raw source results → 1 batched
OpenAI structured extraction → exact evidence/date checks → company normalization /
deduplication → deterministic mandate classification → up to 15 cards → explicit selection
→ existing Company Analysis form → separately authorized fresh analysis`

Sourcing uses the current provider transport/model and cost guards; it never calls
`run_analysis`, stores an analysis report, crawls shortlisted companies or uses saved results
in place of fresh searches. Three search themes cover mandate-specific signals, product/company
launches, and investor/accelerator/funding announcements in the general public-web index.
The source universe is **bounded Tavily general-web results**, not an exhaustive startup database
or a curated publisher whitelist. Every new live request makes new external searches.

- Maximum three searches, ten results per search, thirty extracted candidates, fifteen cards.
- Maximum one model call, 6,000 output tokens and 100,000 serialized input bytes.
- Source input bounded to 1,500 characters per result. Source URLs deduplicated before extraction.
- USD 0.10 estimated admission ceiling; inherited 180-second budget checks/HTTP timeouts.
- No automatic retries, scheduling, background polling, cached-only discovery or batch deep research.
- Empty source results need no model call. Budget/validation failures stop rather than retry.
- The existing single-process lock also prevents simultaneous discovery/analysis operations.

Search parameters were checked against the official
[Tavily search API documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search).
Date-window search filtering assists retrieval; eligibility separately requires an explicit event
DATE in the quoted source. Publication/retrieval timestamps never substitute for an event date.

Sourcing is much cheaper than separately researching each of fifteen companies: at most 3 searches
and 1 model call instead of 45 searches and 30 model calls. Actual token usage/reserved estimate
are returned in the response; the UI displays call counts and the reserved estimate.

## Filters and classification

- Stage: Pre-Seed, Seed, Series A, Series B, Growth, or Any. Known mismatches are excluded;
  missing stage remains a potential match. This is a reported stage, not an inferred current stage.
- Sector: suggested categories and unrestricted custom comma-separated terms. Literal supported
  terms establish relevance; semantic/subsector ambiguity remains a potential match rather than
  a fabricated classification. Sector taxonomy is not a mandatory backend enum.
- Geography: Worldwide, Europe, UK, France, Germany, Nordics, US, North America and custom terms.
  Deterministic country/region containment handles the supported map. Clearly disjoint mapped
  countries are excluded; broad/custom unresolved geography stays potential.
- Business models: optional multi-select; unavailable or ambiguous model remains potential.
- Funding: min/max total and latest round, configurable USD/EUR/GBP thresholds. No FX conversion.
  Unknown funding stays eligible by default; the checkbox can exclude missing/incomparable funding.
- Age: explicit founded year only; after/before bounds are exclusive. Missing year stays potential.
- Signal freshness: inclusive UTC-date cutoff at 7/30/90 days or twelve calendar months;
  future or undated signals are excluded. Signal types are extraction classifications with quotations.
- Include keywords: every requested phrase is checked in the available name/description/signal/sector
  evidence; missing support yields a potential match. Exclusions use deterministic phrase matching.
- Excluded keywords, sectors, geographies and companies/domains. Rejection reasons remain visible.

Cards show MEETS MANDATE, POTENTIAL MATCH — INFORMATION MISSING, or are omitted as OUTSIDE MANDATE.
MEETS means the implemented source-term checks passed, not that diligence confirmed an investment fit.
There are no fit percentages. Why This Surfaced is assembled in Python from the validated signal
quote and filter outcomes, not a second model-generated sales pitch.

## Evidence, identity and limits

Every accepted identity/signal needs an exact quote from a retrieved source. Invalid optional fields
become UNKNOWN. Evidence retains URL, title, publication date when available, retrieval timestamp,
quote, origin host and excerpt hash. Matching quotations verifies transcription, not truth or
semantic attribution. Source text can be wrong or misleading; human review is still necessary.

Company domains are lowercased with `www` removed. Known domains deduplicate regardless of URL path;
normalized names are used when no domain is known. Different known domains are not automatically
merged by fuzzy name. Conflicting structured fields on duplicates become UNKNOWN. Sources do not
increase a confidence score; syndicated copies are never treated as independent confirming votes.
Alias resolution, parent/subsidiary relationships and syndication detection are intentionally limited.

Strict date/currency/scale requirements can exclude relevant companies and produce fewer than 5–15
cards or none. Financial values require literal ISO currency and scale words; tables, `$` ambiguity
and other formats may become UNKNOWN. Sector/business-model synonym matching is conservative;
semantic misses may appear as potential matches. Signal-type/entity/funding meaning still relies on
one unreviewed extraction step. No exhaustive coverage, source truth or perfect matching is promised.

The analysis handoff does not treat lightweight discovery as diligence. It transfers only company
identity and mode. Live analysis must be confirmed separately and performs its own fresh searches.
Founder-market fit and funding remain within the existing Team/Traction analysis framework; no
second analysis schema or parallel memo/financial system was introduced.

## Verification

- Full offline suite: **136 passed in 0.50s**, no failures/skips; one existing Starlette TestClient
  deprecation warning. Includes all 100 prior tests and 36 sourcing cases.
- Cases cover mandate/range validation, filters, unknown funding, dates, exclusions, normalization,
  deduplication, conflicting fields, evidence integrity, grounded explanations, bounded fresh mocked
  searches, demo/live gates, no automatic analysis and both synthetic handoffs.
- Actual headless Chrome sourcing journey passed: two results → evidence inspection → explicit
  handoff → existing analysis and memo; refinement to one result and then zero. No JavaScript errors.
- Browser observed zero automatic analysis calls and exactly one explicit analysis call.
- All provider calls were synthetic/mocked. No paid live requests were made.

Commands:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests
# Optional, with Playwright available and the server running:
node tools/sourcing-browser-smoke.cjs
```

The browser script also accepts `PLAYWRIGHT_MODULE` pointing to an existing Playwright installation.
It uses installed Chrome and cannot trigger live sourcing. Local screenshot: `.local/sourcing-shortlist.png`.

## Files in this change

Created `backend/src/vc_research/sourcing/{__init__,core,offline}.py`,
`backend/src/vc_research/demo/static/sourcing.js`, `backend/tests/test_sourcing.py`,
`tools/sourcing-browser-smoke.cjs` and this document.

Modified `backend/src/vc_research/webapp.py` (one route),
`backend/src/vc_research/demo/static/index.html` and `style.css` (navigation/form/cards),
README.md, SPEC.md and docs/DEMO_GUIDE.md (current scope). Existing analysis JavaScript,
provider, evidence, finance, memo modules and original tests were not changed for sourcing.
