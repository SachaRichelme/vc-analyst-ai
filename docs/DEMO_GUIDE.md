# Demo operation and interview guide

## Acceptance status

Browser UI and offline acceptance: passed. Live-provider acceptance: pending credentials.
No real-company run has been made yet. Do not call the full product DEMO READY until that run passes.

The offline browser harness used an isolated headless Google Chrome session against
http://127.0.0.1:8000. It entered Lumen, clicked Analyze, inspected the rendered report,
selected financial evidence, computed growth/margin/runway and three assumed-multiple
scenarios, downloaded the memo, and checked Lumen Sparse abstention. No JavaScript errors.
Screenshots/receipts are stored locally under ignored `.local/`.

The built-in browser automation tool failed to initialize due to a sandbox kernel error;
Playwright controlling an isolated installed Chrome instance supplied actual browser QA.
No API test has been substituted for that browser test.

## Cost and request bounds

Successful live run: **3 Tavily basic searches + 2 OpenAI calls**, zero retries.
Failed runs may stop earlier. No Tavily Extract, Crawl or Research endpoints are used.
OpenAI calls request at most 6,000 output tokens each; each serialized request is capped
at 100,000 bytes. The model is pinned to `gpt-4.1-mini-2025-04-14`; no autonomous model switching.

Pricing references checked 2026-09-27:

- [Tavily pricing](https://www.tavily.com/pricing): pay-as-you-go USD 0.008 per credit;
  basic search consumes one credit. Three requests therefore cost approximately USD 0.024,
  or may be covered by an account's included credits.
- [OpenAI GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini):
  USD 0.40 per million input tokens and USD 1.60 per million output tokens (uncached rates).

Estimated total = 0.024 + input_tokens × 0.40 / 1,000,000
+ output_tokens × 1.60 / 1,000,000. For illustration, 15,000 input and 5,000 output tokens
across both calls would be about USD 0.038 total. Actual token counts vary and are visible
in the research receipt. This is a pricing estimate, not a guaranteed invoice amount.
The per-run admission estimate reserves USD 0.01 per search and conservatively estimates
model input from serialized bytes. It stops admitting calls above USD 0.20. No daily/global
billing cap is implemented; use provider account controls for account-level limits.

## Suggested companies

**Private-company research: Lightdash, https://www.lightdash.com.** It offers an inspectable
product, open-source context and an official [Series A announcement](https://www.lightdash.com/blogpost/lightdash-raises-series-a).
Use it to discuss product, go-to-market, alternatives, source credibility and unknown economics.
The announcement is historical evidence, not confirmation of its current funding stage.
Fresh research must establish any later developments. Exact URL input avoids namesake confusion.

**Richer public financial disclosure: GitLab, https://about.gitlab.com.** Its
[investor relations](https://ir.gitlab.com/) and
[FY2026 results](https://ir.gitlab.com/news/news-details/2026/GitLab-Reports-Fourth-Quarter-and-Full-Year-Fiscal-Year-2026-Financial-Results-Board-of-Directors-Authorizes-400-million-for-Share-Repurchase-Program/default.aspx)
provide revenue and margin disclosures. This is a public-company financial reference case,
not an early-stage startup or automatically suitable valuation comparable. The bounded
extractor may still abstain on tables or currency shorthand; this live financial case has
not been validated. Use the labeled Lumen fixture to guarantee a reproducible numerical demo.

## Four-minute VC interview script

**0:00–0:30 — Positioning.** “This is a research copilot. It helps me assemble evidence and
prepare diligence; it does not make the investment decision.” Select Live, enter the
company URL and explain the bounded run authorization. Start a run only if deliberately
budgeted; for an interview, prepare a completed live report shortly beforehand.

**0:30–1:30 — Research and evidence.** Show the company/product view. Open one source from
the evidence panel. Explain the difference between a company's own claim and an external
report, and between a reported quote and your investment interpretation. Show retrieval
versus publication time and the research receipt. If the run is still loading, explain the
workflow; avoid promising a fixed completion time.

**1:30–2:30 — Challenge the thesis.** Show Competition, Risks and Critical Unknowns. Choose
one founder question tied to a real evidence gap. Discuss what evidence would change the
view, rather than presenting the generated memo as a recommendation.

**2:30–3:30 — Finance with provenance.** If the live company lacks reliable financials,
show the abstention honestly. Download its memo before replacing the in-memory report.
Switch explicitly to the synthetic Lumen case to demonstrate calculation mechanics:
select C4–C8, confirm the definitions, and show 50% growth, 80% gross margin and 12-month
runway. Mention that the numbers are synthetic and Python computes them. Optional 2/3/4x
multiples are analyst assumptions, not an observed valuation.

**3:30–4:00 — Memo and judgment.** Show the source-linked investment memo and download.
Close with two diligence priorities and one limitation of the research. Sourcing is now a
separate bounded discovery mode (see SOURCING.md); monitoring and more infrastructure remain deferred.
