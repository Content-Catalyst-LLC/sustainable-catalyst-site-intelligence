from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = "sc-international-law-governance/1.0"

SOURCES: List[Dict[str, Any]] = [
    {
        "source_id": "un-security-council-sanctions",
        "title": "United Nations Security Council Consolidated Sanctions List",
        "organization": "United Nations Security Council",
        "base_url": "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list",
        "access_type": "xml_html_pdf",
        "freshness": "event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["sanctions", "international_peace_security", "counterterrorism"],
        "role": "Official consolidated listings, amendments, delistings, and sanctions-regime context.",
        "limitations": "Informational monitoring only; not a commercial screening, legal-advice, or compliance determination service.",
    },
    {
        "source_id": "un-digital-library",
        "title": "United Nations Digital Library",
        "organization": "United Nations",
        "base_url": "https://digitallibrary.un.org",
        "access_type": "metadata_and_documents",
        "freshness": "daily_or_event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["resolutions", "meetings", "voting", "official_documents"],
        "role": "Official UN resolutions, voting records, meeting records, reports, and document metadata.",
        "limitations": "Document publication timing and metadata completeness vary by organ and record type.",
    },
    {
        "source_id": "un-treaty-collection",
        "title": "United Nations Treaty Collection",
        "organization": "United Nations Office of Legal Affairs",
        "base_url": "https://treaties.un.org",
        "access_type": "official_web_records",
        "freshness": "event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["treaties", "ratifications", "reservations", "depositary_actions"],
        "role": "Treaty status, signatures, ratifications, accessions, reservations, declarations, and depositary notifications.",
        "limitations": "The source is authoritative, but integration may rely on structured page or document retrieval rather than a universal public JSON API.",
    },
    {
        "source_id": "eurlex-cellar",
        "title": "EUR-Lex and EU Publications Office Cellar",
        "organization": "European Union Publications Office",
        "base_url": "https://data.europa.eu/data/datasets/sparql-cellar-of-the-publications-office",
        "access_type": "sparql_rest",
        "freshness": "daily",
        "coverage": "European Union",
        "requires_key": False,
        "domains": ["legislation", "case_law", "official_journal", "environmental_law", "human_rights"],
        "role": "EU legislation, case law, official publications, legal metadata, amendments, repeals, and document relationships.",
        "limitations": "Queries must preserve CELEX identifiers, language, document status, and consolidated-versus-original distinctions.",
    },
    {
        "source_id": "curia",
        "title": "Court of Justice of the European Union",
        "organization": "Court of Justice of the European Union",
        "base_url": "https://curia.europa.eu",
        "access_type": "official_case_records",
        "freshness": "event_driven",
        "coverage": "European Union",
        "requires_key": False,
        "domains": ["case_law", "judgments", "opinions", "procedural_updates"],
        "role": "Official judgments, orders, opinions, procedural notices, and case metadata.",
        "limitations": "Publication and machine-readable access vary by record; legal effect depends on procedural posture and authoritative text.",
    },
    {
        "source_id": "icj",
        "title": "International Court of Justice",
        "organization": "International Court of Justice",
        "base_url": "https://www.icj-cij.org",
        "access_type": "official_case_records",
        "freshness": "event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["contentious_cases", "advisory_opinions", "orders", "judgments"],
        "role": "Official case pages, judgments, advisory opinions, orders, press releases, and procedural records.",
        "limitations": "Case status, jurisdictional posture, and authoritative document language must remain visible.",
    },
    {
        "source_id": "icc",
        "title": "International Criminal Court",
        "organization": "International Criminal Court",
        "base_url": "https://www.icc-cpi.int",
        "access_type": "official_case_and_situation_records",
        "freshness": "event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["international_criminal_law", "situations", "cases", "warrants", "decisions"],
        "role": "Official situations, cases, decisions, warrants, filings, and public-information records.",
        "limitations": "Public records must not be used to infer guilt; procedural status and presumption of innocence must remain explicit.",
    },
    {
        "source_id": "ohchr",
        "title": "UN Human Rights Office",
        "organization": "Office of the United Nations High Commissioner for Human Rights",
        "base_url": "https://www.ohchr.org",
        "access_type": "official_reports_and_updates",
        "freshness": "daily_or_event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["human_rights", "treaty_bodies", "special_procedures", "universal_periodic_review"],
        "role": "Human-rights reports, treaty-body records, special-procedure communications, and review documentation.",
        "limitations": "Allegations, findings, recommendations, and final determinations must be clearly distinguished.",
    },
    {
        "source_id": "wto",
        "title": "World Trade Organization",
        "organization": "World Trade Organization",
        "base_url": "https://www.wto.org",
        "access_type": "official_data_and_documents",
        "freshness": "daily_monthly_or_event_driven",
        "coverage": "global",
        "requires_key": False,
        "domains": ["trade_law", "disputes", "notifications", "trade_policy", "environmental_goods"],
        "role": "Trade measures, disputes, notifications, tariff and trade-policy information, and official legal documents.",
        "limitations": "Different WTO systems use different publication schedules and identifiers; legal status must be retained.",
    },
    {
        "source_id": "un-comtrade",
        "title": "UN Comtrade",
        "organization": "United Nations Statistics Division",
        "base_url": "https://comtradeapi.un.org",
        "access_type": "public_api",
        "freshness": "monthly_or_annual",
        "coverage": "global",
        "requires_key": False,
        "domains": ["trade_flows", "sanctions_context", "critical_materials", "environmental_goods"],
        "role": "Trade-flow context for legal, sanctions, supply-chain, and sustainable-development analysis.",
        "limitations": "Commodity classifications, reporting gaps, mirror data, and revisions must remain visible; trade data does not itself establish legal compliance.",
    },
]

MONITORS: List[Dict[str, Any]] = [
    {"monitor_id": "sanctions", "label": "UN sanctions and listing changes", "sources": ["un-security-council-sanctions"], "freshness": "event_driven", "outputs": ["listings", "amendments", "delistings", "regime links"]},
    {"monitor_id": "treaties", "label": "Treaties and depositary actions", "sources": ["un-treaty-collection"], "freshness": "event_driven", "outputs": ["signatures", "ratifications", "accessions", "reservations", "declarations"]},
    {"monitor_id": "un-decisions", "label": "UN resolutions, meetings, and voting", "sources": ["un-digital-library"], "freshness": "daily_or_event_driven", "outputs": ["resolutions", "votes", "meeting records", "official reports"]},
    {"monitor_id": "international-courts", "label": "International courts and tribunals", "sources": ["icj", "icc", "curia"], "freshness": "event_driven", "outputs": ["judgments", "orders", "opinions", "case updates"]},
    {"monitor_id": "human-rights", "label": "Human-rights mechanisms", "sources": ["ohchr"], "freshness": "daily_or_event_driven", "outputs": ["treaty-body records", "special procedures", "UPR", "reports"]},
    {"monitor_id": "eu-law", "label": "EU legislation and case law", "sources": ["eurlex-cellar", "curia"], "freshness": "daily", "outputs": ["legislation", "amendments", "repeals", "case law", "official journal"]},
    {"monitor_id": "trade-governance", "label": "Trade law and economic governance", "sources": ["wto", "un-comtrade"], "freshness": "daily_monthly_or_event_driven", "outputs": ["disputes", "notifications", "trade measures", "trade-flow context"]},
]

NORMALIZED_LEGAL_EVENT_SCHEMA: Dict[str, Any] = {
    "schema": SCHEMA,
    "required": ["source_id", "event_id", "event_type", "title", "published_at", "jurisdiction", "legal_status", "source_url", "retrieved_at"],
    "optional": ["effective_at", "document_id", "instrument", "parties", "subjects", "case_number", "sanctions_regime", "geographies", "related_documents", "language", "caveats", "is_derived"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_registry() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "International Law and Global Governance Source Registry",
        "summary": "Official and public sources for sanctions, treaties, resolutions, courts, human rights, EU law, trade law, and governance monitoring.",
        "counts": {"sources": len(SOURCES), "monitors": len(MONITORS), "no_key_required": sum(not item["requires_key"] for item in SOURCES)},
        "sources": SOURCES,
    }


def overview() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "International Law and Global Governance Monitor",
        "summary": "A source-aware public monitor for legal instruments, institutional decisions, sanctions, treaties, courts, human rights, and trade governance.",
        "monitors": MONITORS,
        "sources": SOURCES,
        "freshness_labels": ["event_driven", "daily", "monthly", "periodic", "last_known_good", "temporarily_unavailable"],
        "governance": [
            "Present official records and procedural status without offering legal advice or compliance determinations.",
            "Distinguish allegations, interim measures, orders, judgments, recommendations, and final decisions.",
            "Do not infer guilt, liability, sanctions applicability, treaty obligations, or individual legal status from summary data.",
            "Retain document identifiers, jurisdiction, authoritative source links, publication date, and legal status.",
            "Treat trade and statistical data as context rather than proof of legal compliance or breach.",
        ],
    }


def monitor_detail(monitor_id: str) -> Dict[str, Any]:
    monitor = next((item for item in MONITORS if item["monitor_id"] == monitor_id), None)
    if not monitor:
        raise KeyError(monitor_id)
    source_ids = set(monitor["sources"])
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": monitor["label"],
        "monitor": monitor,
        "sources": [item for item in SOURCES if item["source_id"] in source_ids],
        "public_status": "registered_source_monitor",
        "records": [],
        "notice": "This release establishes source, schema, status, and public-display contracts. Live record ingestion is connector-specific and must retain authoritative-source links and legal-status metadata.",
    }


def sanctions_monitor() -> Dict[str, Any]:
    payload = monitor_detail("sanctions")
    payload.update({
        "title": "UN Sanctions Monitor",
        "fields": ["regime", "listed_name", "entity_type", "listing_date", "amendment_date", "delisting_date", "measures", "official_reason_link"],
        "safety_note": "Informational official-record monitor only; not a substitute for sanctions screening, legal advice, or compliance controls.",
    })
    return payload


def legal_events(event_type: Optional[str] = None, jurisdiction: Optional[str] = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "International Law Event Stream",
        "filters": {"event_type": event_type, "jurisdiction": jurisdiction},
        "records": [],
        "supported_event_types": ["listing", "delisting", "resolution", "vote", "treaty_action", "judgment", "order", "opinion", "legislation", "notification", "report"],
        "record_schema": NORMALIZED_LEGAL_EVENT_SCHEMA,
        "notice": "No synthetic legal conclusions are produced. Records must originate from cited authoritative sources.",
    }


def methodology() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "International Law and Governance Methodology",
        "normalized_legal_event_schema": NORMALIZED_LEGAL_EVENT_SCHEMA,
        "status_taxonomy": ["published", "adopted", "in_force", "pending", "interim", "final", "amended", "repealed", "withdrawn", "delisted", "unknown"],
        "methods": [
            "Use official institutional records as the primary source.",
            "Preserve authoritative identifiers such as UN symbols, treaty registration numbers, CELEX identifiers, and case numbers.",
            "Keep publication, adoption, entry-into-force, amendment, and repeal dates separate.",
            "Label machine-extracted metadata and derived relationships explicitly.",
            "Show last-known-good and unavailable states rather than silently dropping a legal source.",
            "Require human review before publishing summaries that characterize legal effect, responsibility, or compliance.",
        ],
        "excluded_uses": ["legal advice", "commercial sanctions screening", "eligibility determinations", "automated guilt or liability judgments", "unreviewed compliance conclusions"],
    }


def export_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "generated_at": _now(),
        "version_scope": "v1.10.0",
        "schema": SCHEMA,
        "title": "International Law and Governance Export",
        "formats": ["json", "csv_ready"],
        "datasets": ["sources", "monitors", "legal_event_schema", "status_taxonomy", "methodology"],
        "sources": SOURCES,
        "monitors": MONITORS,
        "legal_event_schema": NORMALIZED_LEGAL_EVENT_SCHEMA,
        "methodology": methodology()["methods"],
        "public_safety": "Exports provide source-aware official-record context and must not be represented as legal advice or compliance certification.",
    }
