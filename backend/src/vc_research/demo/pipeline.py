import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from ..domain.evidence import Company, Source, SourceVersion, Passage, Claim, ClaimEvidence, TextValue, MissingValue, MissingReason
from .finance import candidate_value, initial_finance
from .live import RunError, safe_url
from .models import SECTIONS


def host(url):
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def build_evidence(requested, extraction, sources, mode):
    website = safe_url(extraction.website)
    if not extraction.identity_resolved or not website:
        raise RunError("Company identity was not resolved. Use the exact company website. " + extraction.identity_reason[:300])
    requested_url = requested if "://" in requested else "https://" + requested if "." in requested and " " not in requested else None
    if requested_url and host(requested_url) != host(website):
        raise RunError("Returned company website does not match the requested host. Check the official URL.")
    if not any(host(s["url"]) == host(website) for s in sources):
        raise RunError("No source from the identified company website was retrieved. Use its exact official URL.")
    now = datetime.now(timezone.utc)
    company = Company(id=uuid4(), mode=mode, name=extraction.company_name, website=website, first_seen_at=now)
    graph = {"company": company.model_dump(mode="json"), "sources": [], "source_versions": [], "passages": [], "claims": [], "claim_evidence": []}
    source_map = {}
    for item in sources:
        source = Source(id=uuid4(), mode=mode, url=item["url"], publisher=host(item["url"]),
            source_type="company" if host(item["url"]) == host(website) else "other",
            origin_group=host(item["url"]), retention="excerpt", model_processing_allowed=True,
            export_allowed=False, rights_basis="Provider-supplied research excerpt; downstream republication rights not independently reviewed" if mode == "live" else "Synthetic project-owned fixture")
        published = None
        if item.get("published_at"):
            try:
                published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = None
            except (ValueError, TypeError):
                pass
        version = SourceVersion(id=uuid4(), mode=mode, source_id=source.id, title=item["title"],
            content_hash=hashlib.sha256(item["text"].encode()).hexdigest(), published_at=published,
            retrieved_at=item["retrieved_at"], last_checked_at=now, extractor_version="bounded-excerpts-1")
        source_map[item["id"]] = (item, source, version)
        graph["sources"].append(source.model_dump(mode="json"))
        graph["source_versions"].append(version.model_dump(mode="json"))
    cards, candidates, rejected, seen = [], [], 0, set()
    for fact in extraction.facts:
        entry = source_map.get(fact.source_id)
        if not entry or fact.quote not in entry[0]["text"] or (fact.source_id, fact.quote) in seen:
            rejected += 1
            continue
        seen.add((fact.source_id, fact.quote))
        item, source, version = entry
        passage = Passage(id=uuid4(), mode=mode, source_version_id=version.id, excerpt=fact.quote,
                          locator="Exact substring of bounded " + item["coverage"], extraction_version="exact-quote-1")
        claim = Claim(id=uuid4(), mode=mode, company_id=company.id, predicate=fact.section,
            value=TextValue(value=fact.quote), statement_class="COMPANY CLAIM" if source.source_type == "company" else "FACT",
            derivation="reported", verification="unreviewed", as_of=now,
            confidence_reasons=("Exact quotation verified against provider excerpt; factual truth, identity attribution and independence need analyst review",))
        edge = ClaimEvidence(id=uuid4(), mode=mode, claim_id=claim.id, passage_id=passage.id,
            relationship="supports", authority_for_claim="Company self-report" if source.source_type == "company" else "External report; authority not independently verified",
            directness="Exact quotation", independence="unknown", reasoning="Quote supports only what this source reports, not its factual accuracy")
        label = f"C{len(cards)+1}"
        cards.append({"id": label, "claim_uuid": str(claim.id), "section": fact.section, "quote": fact.quote,
                      "source_id": fact.source_id, "source_url": item["url"], "source_title": item["title"],
                      "class": claim.statement_class, "verification": "unreviewed", "coverage": item["coverage"]})
        for key, record in (("passages", passage), ("claims", claim), ("claim_evidence", edge)):
            graph[key].append(record.model_dump(mode="json"))
        if fact.financial:
            try:
                value = candidate_value(fact.financial, fact.quote)
                candidates.append({**fact.financial.model_dump(), "id": label, "claim_uuid": str(claim.id),
                                   "value": str(value), "quote": fact.quote, "source_id": fact.source_id})
            except ValueError:
                rejected += 1
    if not cards:
        raise RunError("No exact, source-linked claims survived extraction checks. No memo was generated.")
    for candidate in candidates:
        peers = [c for c in candidates if (c["metric"], c["period"], c["currency"]) == (candidate["metric"], candidate["period"], candidate["currency"])]
        candidate["conflicted"] = len({p["value"] for p in peers}) > 1
    return graph, cards, candidates, rejected


def validate_analysis(analysis, cards):
    if len({s.title for s in analysis.sections}) != len(SECTIONS):
        raise RunError("Analysis omitted or duplicated a required section; no memo was published.")
    valid = {c["id"] for c in cards}
    notes = [n for s in analysis.sections for n in s.notes] + analysis.founder_questions + [analysis.bull, analysis.base, analysis.bear]
    for note in notes:
        if set(note.claim_ids) - valid or (note.kind == "INFERENCE" and not note.claim_ids):
            raise RunError("Analysis contains an unsupported citation; no memo was published.")
    return analysis


def memo_markdown(report):
    lines = [f'# {report["company"]} — investment research memo', "",
             f'Mode: {report["mode"].upper()} | Researched: {report["generated_at"]}', "",
             "Draft for analyst review. Investment judgment remains with the analyst.", ""]
    if report["mode"] == "demo":
        lines += ["SYNTHETIC FIXTURE — not real company research.", ""]
    for section in report["analysis"]["sections"]:
        lines += [f'## {section["title"]}', ""]
        for note in section["notes"]:
            lines.append(f'- **{note["kind"]}**: {note["text"]} ' + " ".join(f'[{c}]' for c in note["claim_ids"]))
        lines.append("")
    lines += ["## Bull / Base / Bear", ""]
    for key in ("bull", "base", "bear"):
        note = report["analysis"][key]
        lines += [f'**{key.title()} ({note["kind"]})**: {note["text"]} ' + " ".join(f'[{c}]' for c in note["claim_ids"]), ""]
    lines += ["## Financial analysis and valuation", "", report["financials"]["reason"], ""]
    for item in report["financials"]["calculations"]:
        record = item["record"]
        lines += [f'- CALCULATED VALUE: {record["formula"]} = {record["result"]} {record["output_unit"]}. Formula: {item["formula"]}. ' + " ".join(f'[{c}]' for c in item["claim_ids"])]
        for value in record["inputs"]:
            lines.append(f'  - {value["name"]}: {value["value"]} {value["unit"]}; ' + ("ASSUMPTION: " + value["assumption"] if value["assumption"] else "source claim " + value["claim_id"]))
    lines += ["", report["financials"]["valuation"], "", report["financials"]["dcf"], "", "## Founder questions", ""]
    for note in report["analysis"]["founder_questions"]:
        lines.append(f'- {note["text"]} ' + " ".join(f'[{c}]' for c in note["claim_ids"]))
    lines += ["", "## Evidence and sources", "", "Quotes are visible in the local evidence panel. Export includes links and lineage; republication rights are not asserted.", ""]
    for card in report["evidence"]:
        # Plain links avoid injection into markdown link labels from external titles.
        lines.append(f'- [{card["id"]}] {card["class"]}, {card["verification"]}; {card["section"]}; {card["source_url"]}')
    lines += ["", "## Limitations", ""] + ["- " + x for x in report["limitations"]]
    return "\n".join(lines)


def run_analysis(company, provider, mode):
    sources = provider.research(company)
    extraction = provider.extract(company, sources)
    graph, cards, candidates, rejected = build_evidence(company, extraction, sources, mode)
    analysis = validate_analysis(provider.analyze(extraction.company_name, cards), cards)
    # Preserve Step 1 missing-data semantics in the report, without claiming universal absence.
    unknowns = []
    for section in analysis.sections:
        for note in section.notes:
            if note.kind == "UNKNOWN":
                unknowns.append(Claim(id=uuid4(), mode=mode, company_id=graph["company"]["id"],
                    predicate=section.title, value=MissingValue(reason=MissingReason.NOT_FOUND, explanation=note.text),
                    statement_class="UNKNOWN", derivation="unknown", verification="unreviewed",
                    as_of=datetime.now(timezone.utc)).model_dump(mode="json"))
    graph["claims"].extend(unknowns)
    report = {"run_id": str(uuid4()), "company": extraction.company_name, "website": extraction.website,
        "mode": mode, "generated_at": datetime.now(timezone.utc).isoformat(), "analysis": analysis.model_dump(),
        "evidence": cards, "sources": [{k:v for k,v in s.items() if k != "text"} for s in sources],
        "evidence_graph": graph, "financial_candidates": candidates, "financials": initial_finance(candidates),
        "usage": provider.usage(), "rejected_extractions": rejected,
        "limitations": ["Bounded public-web review, not complete due diligence. Not-found findings refer only to reviewed sources.",
            "Fresh search requests do not guarantee every page is current or that the provider recrawled it today. Retrieval time is not publication time.",
            "Exact quotes and citation IDs are checked in code. Semantic support, source credibility, company attribution and independence still need human review.",
            "Financial extraction is conservative. Review source meaning, scale, currency and period comparability before using calculations.",
            "No normalized peer dataset or forecast model: comparable valuation and DCF may be unavailable. No automatic investment decision."]}
    if mode == "demo":
        report["limitations"].insert(0, "All company details, sources and conclusions in this mode are synthetic fixtures. No external requests were made.")
    report["memo_markdown"] = memo_markdown(report)
    return report
