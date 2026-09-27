"""Explicit, synthetic browser walkthrough. Never a fallback for live research."""
from .models import Extraction, Analysis, SECTIONS
from .live import RunError

QUOTES = [
    ("Team", "Lumen Fixture Software was founded by two former logistics operators.", None),
    ("Product", "Lumen Fixture Software provides shipment exception software for regional distributors.", None),
    ("Business Model", "The synthetic company charges an annual software subscription per warehouse.", None),
    ("Traction", "Reported revenue was USD 2 million for FY2024.", ("revenue", "2", "million", "FY2024")),
    ("Traction", "Reported revenue was USD 3 million for FY2025.", ("revenue", "3", "million", "FY2025")),
    ("Traction", "Reported gross profit was USD 2.4 million for FY2025.", ("gross_profit", "2.4", "million", "FY2025")),
    ("Traction", "Cash was USD 1.2 million at 2025-12-31.", ("cash", "1.2", "million", "2025-12-31")),
    ("Traction", "Average monthly net burn was USD 100 thousand in Q4 2025.", ("monthly_net_burn", "100", "thousand", "Q4 2025")),
    ("Market", "The synthetic product targets regional distributors with multiple warehouses.", None),
    ("Competition", "Customers compare the product with spreadsheets and ERP exception modules.", None),
    ("Why Now", "The company attributes buyer interest to increasing delivery reporting requirements.", None),
    ("Risks", "The largest customer represented 35 percent of revenue in FY2025.", None),
]

class OfflineProvider:
    def __init__(self, requested):
        self.sparse = requested.strip().lower() == "lumen sparse"
        if requested.strip().lower() not in {"lumen", "lumen sparse", "https://lumen.example", "https://lumen.example/"}:
            raise RunError("Offline mode accepts only 'Lumen' (synthetic financial case) or 'Lumen Sparse' (missing data). Select Live for a real company.")
        self.rows = [r for r in QUOTES if not self.sparse or r[2] is None]

    def research(self, company):
        return [{"id": "S1", "url": "https://lumen.example/", "title": "Lumen — synthetic company briefing",
                 "text": "\n".join(r[1] for r in self.rows), "retrieved_at": "2026-09-26T12:00:00+00:00",
                 "published_at": None, "coverage": "synthetic fixture; not an external page"}]

    def extract(self, company, sources):
        facts = []
        for section, quote, metric in self.rows:
            financial = dict(zip(("metric", "amount", "scale", "period"), metric)) | {"currency": "USD"} if metric else None
            facts.append({"source_id": "S1", "section": section, "quote": quote, "financial": financial})
        return Extraction(company_name="Lumen Fixture Software", website="https://lumen.example/",
            identity_resolved=True, identity_reason="Explicit synthetic fixture", facts=facts)

    def analyze(self, company, claims):
        def note(text, section):
            return {"text": text, "kind": "INFERENCE", "claim_ids": [c["id"] for c in claims if c["section"] == section][:2]}
        unknown = {"text": "Retention, acquisition costs and independently verified customer outcomes were not found in the synthetic briefing.", "kind": "UNKNOWN", "claim_ids": []}
        texts = {
            "Team": "Operating experience may help identify workflow pain; technical execution and sales leadership still need diligence.",
            "Product": "A focused exception workflow could support a narrow initial use case. Validate time saved with customer references.",
            "Business Model": "Warehouse-based subscriptions suggest recurring revenue potential; contract duration alone does not establish retention.",
            "Traction": "Reported financial figures are candidates for review, not audited evidence. Check revenue recognition and period comparability.",
            "Market": "The stated customer segment supports a bottom-up sizing exercise, but customer counts and achievable annual spend are missing.",
            "Competition": "ERP modules and spreadsheets are plausible substitution risks. Test willingness to pay for a standalone product.",
            "Why Now": "The timing thesis depends on the company's reporting-requirements claim; validate actual buying urgency.",
            "Risks": "Customer concentration could magnify renewal risk; test the downside of losing the largest account.",
        }
        sections = [{"title": s, "notes": [note(texts[s], s) if s in texts and any(c["section"] == s for c in claims) else unknown]} for s in SECTIONS]
        return Analysis.model_validate({"sections": sections, "founder_questions": [
            note("How would losing the largest customer change revenue and spending plans?", "Risks"),
            note("Why do customers pay separately rather than use their existing ERP module?", "Competition"),
            {"text": "Provide retention by customer cohort and reconcile the customer-level data with reported revenue.", "kind": "UNKNOWN", "claim_ids": []}],
            "bull": note("If the specialized workflow demonstrably saves customers time, a focused product could earn renewals and expansion.", "Product"),
            "base": note("The subscription proposition remains plausible; renewal behavior must be established before underwriting growth.", "Business Model"),
            "bear": note("A large-account loss could expose concentration risk before the company diversifies its customer base.", "Risks")})

    def usage(self):
        return {"searches": 0, "model_calls": 0, "input_tokens": 0, "output_tokens": 0,
                "reserved_estimate_usd": 0, "queries": [], "model": "synthetic fixture", "retries": 0}
