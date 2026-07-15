from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .source_methodology_studio import METHODOLOGY_RECORDS, SOURCE_RECORDS
from .version import APP_VERSION, API_SCHEMA_VERSION, RELEASE_NAME

OBSERVATORY_SCHEMA = "sc-auditable-public-observatory/2.0"
AUDIT_RECORD_SCHEMA = "sc-public-evidence-record/2.0"
AUDIT_PACKET_SCHEMA = "sc-public-observatory-packet/2.0"
LINEAGE_SCHEMA = "sc-public-lineage/2.0"
VERIFICATION_SCHEMA = "sc-public-integrity-verification/2.0"
INTEGRITY_ALGORITHM = "sha256"
MAX_VERIFICATION_BYTES = 262_144

SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|password|secret|token|authorization|cookie|session|private[_-]?url|"
    r"environment|stack[_-]?trace|retry[_-]?queue|credential)",
    re.IGNORECASE,
)

PUBLIC_WORKSPACES: list[dict[str, str]] = [
    {
        "id": "observatory",
        "title": "Auditable Public Observatory",
        "route": "/app/?view=observatory",
        "summary": "Inspect evidence records, lineage, integrity digests, release history, and verification limits.",
    },
    {
        "id": "overview",
        "title": "Global Observatory",
        "route": "/app/?view=overview",
        "summary": "Map-first satellite context, public event signals, and country evidence.",
    },
    {
        "id": "economics",
        "title": "Economics, Markets, and Sustainability Signals",
        "route": "/app/?view=economics",
        "summary": "Inspect official economic, trade, labour, energy, demographic, company-filing, and sustainability records with source and timing context.",
    },
    {
        "id": "law",
        "title": "International Law and Global Governance Observatory",
        "route": "/app/?view=law",
        "summary": "Inspect official legal and governance records with authority type, procedural status, official symbols, citations, and source context preserved.",
    },
    {
        "id": "science",
        "title": "Scientific and Earth Systems Observatory",
        "route": "/app/?view=science",
        "summary": "Discover scientific records, assets, map layers, STAC items, and time series with mission, quality, license, attribution, and observation context preserved.",
    },
    {
        "id": "humanitarian",
        "title": "Humanitarian, Conflict, and Displacement Observatory",
        "route": "/app/?view=humanitarian",
        "summary": "Connect public humanitarian, conflict, displacement, protection, and hazard evidence without fabricated crisis records or hidden responsible-data limits.",
    },
    {
        "id": "earth",
        "title": "Earth Observation Studio",
        "route": "/app/?view=earth",
        "summary": "Compare satellite-derived layers across dates with source and imagery limits.",
    },
    {
        "id": "events",
        "title": "Live Event Intelligence",
        "route": "/app/?view=events",
        "summary": "Filter public hazard and humanitarian records while retaining source identity.",
    },
    {
        "id": "country",
        "title": "Global Country Intelligence",
        "route": "/app/?view=country&country=KEN",
        "summary": "Explore country indicators, trends, event context, and reporting-year differences.",
    },
    {
        "id": "compare",
        "title": "Comparative Intelligence",
        "route": "/app/?view=compare&country=KEN&compare=GHA",
        "summary": "Align two-country evidence without hiding units, dates, definitions, or missing values.",
    },
    {
        "id": "thematic",
        "title": "Thematic Intelligence Dashboards",
        "route": "/app/?view=thematic&dashboard=climate-environment&country=KEN",
        "summary": "Focused climate, development, security, and infrastructure research views.",
    },
    {
        "id": "briefing",
        "title": "Public Briefing and Export Studio",
        "route": "/app/?view=briefing&briefType=country&country=KEN",
        "summary": "Generate deterministic source-aware briefs and portable evidence exports.",
    },
    {
        "id": "sources",
        "title": "Source and Methodology Studio",
        "route": "/app/?view=sources",
        "summary": "Inspect source coverage, delivery state, methodology, and known limitations.",
    },
    {
        "id": "saved",
        "title": "Saved Views and Research Paths",
        "route": "/app/?view=saved",
        "summary": "Preserve public interface state locally and exchange portable research paths.",
    },
]

AUDIT_ARTIFACTS: list[dict[str, Any]] = [
    {
        "id": "source-registry",
        "title": "Public source registry",
        "artifact_type": "registry",
        "route": "/app/?view=sources",
        "schema": "sc-source-methodology/1.0",
        "source_ids": [record["id"] for record in SOURCE_RECORDS],
        "methodology_ids": ["delivery-states", "cache-behavior", "optional-source-failures"],
        "verification_level": "registry-and-cross-reference",
        "limitations": ["Connector availability can change after the registry snapshot is generated."],
    },
    {
        "id": "methodology-registry",
        "title": "Public methodology registry",
        "artifact_type": "registry",
        "route": "/app/?view=sources",
        "schema": "sc-source-methodology/1.0",
        "source_ids": sorted({source_id for record in METHODOLOGY_RECORDS for source_id in record.get("source_ids", [])}),
        "methodology_ids": [record["id"] for record in METHODOLOGY_RECORDS],
        "verification_level": "implementation-reference",
        "limitations": ["Methodology records describe application behavior but do not certify an external source methodology."],
    },
    {
        "id": "international-law-governance",
        "title": "International Law and Global Governance Observatory",
        "artifact_type": "workspace",
        "route": "/app/?view=law",
        "schema": "sc-international-law-observatory/1.0",
        "source_ids": ["platform-core"],
        "methodology_ids": ["delivery-states", "optional-source-failures"],
        "verification_level": "official-record-and-authority-linked",
        "limitations": [
            "Authority classifications preserve source metadata but do not independently establish binding legal effect.",
            "The workspace provides public research context and is not legal advice or a compliance determination.",
        ],
    },
    {
        "id": "scientific-earth-systems",
        "title": "Scientific and Earth Systems Observatory",
        "artifact_type": "workspace",
        "route": "/app/?view=science",
        "schema": "sc-site-intelligence-scientific-earth-systems/1.0",
        "source_ids": ["platform-core"],
        "methodology_ids": ["delivery-states", "optional-source-failures", "imagery-interpretation", "missing-values"],
        "verification_level": "scientific-record-and-data-fabric-linked",
        "limitations": [
            "Metadata discovery is not equivalent to scientific validation or peer review.",
            "Forecasts, observations, model products, catalog records, and computed properties remain distinct.",
        ],
    },
    {
        "id": "humanitarian-conflict-displacement",
        "title": "Humanitarian, Conflict, and Displacement Observatory",
        "artifact_type": "workspace",
        "route": "/app/?view=humanitarian",
        "schema": "sc-site-intelligence-humanitarian-conflict-displacement/1.0",
        "source_ids": ["platform-core", "reliefweb", "usgs-earthquakes", "nasa-eonet"],
        "methodology_ids": ["delivery-states", "optional-source-failures", "event-deduplication", "country-event-matching", "missing-values"],
        "verification_level": "source-record-and-responsible-data-linked",
        "limitations": [
            "Public humanitarian and conflict records are incomplete and source-dependent.",
            "The workspace does not infer legal responsibility, protection status, eligibility, individual risk, or operational priority.",
        ],
    },
    {
        "id": "earth-observation",
        "title": "Earth Observation Studio",
        "artifact_type": "workspace",
        "route": "/app/?view=earth",
        "schema": "sc-earth-observation/1.0",
        "source_ids": ["nasa-gibs", "openstreetmap"],
        "methodology_ids": ["earth-date-validation", "imagery-interpretation", "delivery-states"],
        "verification_level": "source-and-method-linked",
        "limitations": ["Rendered imagery is contextual and is not a substitute for ground validation."],
    },
    {
        "id": "live-events",
        "title": "Unified Live Event Intelligence",
        "artifact_type": "workspace",
        "route": "/app/?view=events",
        "schema": "sc-public-events/1.0",
        "source_ids": ["usgs-earthquakes", "nasa-eonet", "reliefweb"],
        "methodology_ids": ["country-event-matching", "event-deduplication", "optional-source-failures"],
        "verification_level": "source-record-linked",
        "limitations": ["The event workspace is not an emergency alert or operational incident system."],
    },
    {
        "id": "country-intelligence",
        "title": "Global Country Intelligence",
        "artifact_type": "workspace",
        "route": "/app/?view=country&country=KEN",
        "schema": "sc-country-intelligence/1.0",
        "source_ids": ["world-bank", "usgs-earthquakes", "nasa-eonet", "reliefweb", "nasa-gibs"],
        "methodology_ids": ["latest-value-selection", "missing-values", "country-normalization", "trend-construction"],
        "verification_level": "field-level-provenance",
        "limitations": ["Different indicators can retain different reporting years and source definitions."],
    },
    {
        "id": "comparative-intelligence",
        "title": "Comparative Intelligence",
        "artifact_type": "workspace",
        "route": "/app/?view=compare&country=KEN&compare=GHA",
        "schema": "sc-comparative-intelligence/1.0",
        "source_ids": ["world-bank", "usgs-earthquakes", "nasa-eonet", "reliefweb"],
        "methodology_ids": ["indicator-compatibility", "reporting-year-differences", "comparison-calculations", "missing-values"],
        "verification_level": "compatibility-gated",
        "limitations": ["Mathematical compatibility does not establish causal or policy equivalence."],
    },
    {
        "id": "thematic-dashboards",
        "title": "Thematic Intelligence Dashboards",
        "artifact_type": "workspace",
        "route": "/app/?view=thematic&dashboard=climate-environment&country=KEN",
        "schema": "sc-thematic-intelligence/1.0",
        "source_ids": ["world-bank", "nasa-gibs", "usgs-earthquakes", "nasa-eonet", "reliefweb"],
        "methodology_ids": ["latest-value-selection", "trend-construction", "imagery-interpretation", "optional-source-failures"],
        "verification_level": "dashboard-manifest",
        "limitations": ["Dashboard groupings do not create a proprietary composite score or ranking."],
    },
    {
        "id": "briefing-manifest",
        "title": "Public briefing investigation manifest",
        "artifact_type": "export-contract",
        "route": "/app/?view=briefing&briefType=country&country=KEN",
        "schema": "sc-public-investigation/1.0",
        "source_ids": [record["id"] for record in SOURCE_RECORDS if "briefing" in record.get("features", [])],
        "methodology_ids": ["brief-generation", "export-generation", "missing-values"],
        "verification_level": "portable-evidence-manifest",
        "limitations": ["An integrity digest detects changes to a packet; it does not prove publisher identity or factual correctness."],
    },
    {
        "id": "saved-view-contract",
        "title": "Saved view manifest contract",
        "artifact_type": "schema-contract",
        "route": "/app/?view=saved",
        "schema": "sc-saved-view/1.0",
        "source_ids": [],
        "methodology_ids": ["export-generation"],
        "verification_level": "schema-validation",
        "limitations": ["Saved views preserve public interface state, not a complete evidence snapshot."],
    },
    {
        "id": "public-release-record",
        "title": "Public launch and portfolio record",
        "artifact_type": "release-record",
        "route": "/app/?view=launch",
        "schema": "sc-site-intelligence-portfolio/1.0",
        "source_ids": [],
        "methodology_ids": [],
        "verification_level": "release-manifest",
        "limitations": ["Portfolio metadata describes the project and does not certify production uptime or external connector availability."],
    },
]

RELEASE_LEDGER = [
    {"version": "1.18.0", "title": "Global Country Intelligence", "audit_contribution": "Country evidence records and source identity."},
    {"version": "1.19.0", "title": "Comparative Intelligence", "audit_contribution": "Compatibility states and withheld calculations."},
    {"version": "1.20.0", "title": "Public Briefing and Export Studio", "audit_contribution": "Canonical investigation manifests and portable exports."},
    {"version": "1.21.0", "title": "Thematic Intelligence Dashboards", "audit_contribution": "Source-aware cross-domain dashboard manifests."},
    {"version": "1.22.0", "title": "Source and Methodology Studio", "audit_contribution": "Public source and methodology registries."},
    {"version": "1.23.0", "title": "Saved Views and Shareable Research Paths", "audit_contribution": "Portable browser-local view manifests."},
    {"version": "1.24.0", "title": "Accessibility, Performance, and Mobile", "audit_contribution": "Public delivery diagnostics and explicit quality budgets."},
    {"version": "1.25.0", "title": "Public Launch and Portfolio", "audit_contribution": "Public product record and launch checklist."},
    {"version": "2.0.0", "title": "Auditable Public Observatory", "audit_contribution": "Evidence ledger, lineage graph, integrity digests, and public verification contract."},
    {"version": "2.1.0", "title": "Global Conditions and Live Map Observatory", "audit_contribution": "Core-powered public geographic records, observation signals, map-layer registry integration, and explicit fallback states."},
    {"version": "2.2.0", "title": "Economics, Markets, and Sustainability Signals", "audit_contribution": "Core-backed official-statistics records, timing classifications, source-preserving comparisons, geography mapping, and explicit no-real-time-market-data boundaries."},
    {"version": "2.3.0", "title": "International Law and Global Governance Observatory", "audit_contribution": "Core-backed official legal records, legal-authority taxonomy, procedural-status preservation, source-aware country profiles, timelines, and explicit non-advice boundaries."},
    {"version": "2.4.0", "title": "Scientific and Earth Systems Observatory", "audit_contribution": "Core-backed scientific records, scientific assets, map layers, STAC discovery, time-series access, source and quality preservation, and explicit no-fabrication boundaries."},
    {"version": "2.5.0", "title": "Humanitarian, Conflict, and Displacement Observatory", "audit_contribution": "Source-aware crisis, displacement, civilian-protection, humanitarian access, and hazard evidence with no-fabrication and responsible-data safeguards."},
]


class ObservatoryError(ValueError):
    """Raised for invalid public observatory requests."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def integrity_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                return True
            if _contains_sensitive_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _artifact_template(artifact_id: str) -> dict[str, Any]:
    for item in AUDIT_ARTIFACTS:
        if item["id"] == artifact_id:
            return item
    raise ObservatoryError(f"Unknown public audit artifact: {artifact_id}")


def audit_record(artifact_id: str) -> dict[str, Any]:
    template = _artifact_template(artifact_id)
    core = {
        "schema": AUDIT_RECORD_SCHEMA,
        "artifact_id": template["id"],
        "title": template["title"],
        "artifact_type": template["artifact_type"],
        "route": template["route"],
        "artifact_schema": template["schema"],
        "application_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "source_ids": sorted(set(template.get("source_ids", []))),
        "methodology_ids": sorted(set(template.get("methodology_ids", []))),
        "verification_level": template["verification_level"],
        "data_state": "registered-public-contract",
        "limitations": template.get("limitations", []),
    }
    return {
        **core,
        "generated_at": _utc_now(),
        "integrity": {
            "algorithm": INTEGRITY_ALGORITHM,
            "digest": integrity_digest(core),
            "canonicalization": "UTF-8 JSON with sorted keys and compact separators",
            "scope": "All record fields except generated_at and integrity",
        },
    }


def audit_catalog() -> dict[str, Any]:
    records = [audit_record(item["id"]) for item in AUDIT_ARTIFACTS]
    return {
        "ok": True,
        "schema": OBSERVATORY_SCHEMA,
        "application_version": APP_VERSION,
        "generated_at": _utc_now(),
        "record_count": len(records),
        "records": records,
    }


def lineage_graph() -> dict[str, Any]:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []

    for source in SOURCE_RECORDS:
        nodes.append({"id": f"source:{source['id']}", "type": "source", "label": source["name"]})
    for method in METHODOLOGY_RECORDS:
        nodes.append({"id": f"method:{method['id']}", "type": "methodology", "label": method["title"]})
    for workspace in PUBLIC_WORKSPACES:
        nodes.append({"id": f"workspace:{workspace['id']}", "type": "workspace", "label": workspace["title"]})
    for artifact in AUDIT_ARTIFACTS:
        artifact_node = f"artifact:{artifact['id']}"
        nodes.append({"id": artifact_node, "type": "audit-artifact", "label": artifact["title"]})
        route_view = artifact["route"].split("view=", 1)[-1].split("&", 1)[0]
        if any(workspace["id"] == route_view for workspace in PUBLIC_WORKSPACES):
            edges.append({"from": artifact_node, "to": f"workspace:{route_view}", "relation": "documents"})
        for source_id in sorted(set(artifact.get("source_ids", []))):
            edges.append({"from": f"source:{source_id}", "to": artifact_node, "relation": "supports"})
        for method_id in sorted(set(artifact.get("methodology_ids", []))):
            edges.append({"from": f"method:{method_id}", "to": artifact_node, "relation": "governs"})

    core = {
        "schema": LINEAGE_SCHEMA,
        "application_version": APP_VERSION,
        "nodes": sorted(nodes, key=lambda item: item["id"]),
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"], item["relation"])),
    }
    return {
        "ok": True,
        **core,
        "generated_at": _utc_now(),
        "integrity": {"algorithm": INTEGRITY_ALGORITHM, "digest": integrity_digest(core)},
    }


def observatory_profile() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": OBSERVATORY_SCHEMA,
        "application_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "release": "Auditable Public Observatory",
        "release_status": "auditable-public-observatory",
        "positioning": (
            "Sustainable Catalyst Site Intelligence is an auditable public observatory that keeps public evidence, "
            "source identity, methodology, data state, lineage, and integrity limits visible across research workflows."
        ),
        "principles": [
            "Every registered public output links to a source, method, schema, or explicit limitation.",
            "Integrity digests detect changes but do not prove truth, authenticity, or institutional endorsement.",
            "Missing data, reporting-year differences, and optional-source failures remain visible.",
            "Public verification is structural and does not persist submitted records.",
            "Platform Core remains optional for public reading and deployment.",
        ],
        "workspaces": PUBLIC_WORKSPACES,
        "audit_capabilities": [
            "public evidence-record catalog",
            "source-method-workspace lineage graph",
            "SHA-256 canonical-record digests",
            "non-persistent payload verification",
            "release ledger",
            "JSON and Markdown audit packet exports",
        ],
        "counts": {
            "workspaces": len(PUBLIC_WORKSPACES),
            "audit_artifacts": len(AUDIT_ARTIFACTS),
            "registered_sources": len(SOURCE_RECORDS),
            "methodology_records": len(METHODOLOGY_RECORDS),
            "release_milestones": len(RELEASE_LEDGER),
        },
        "responsible_use": {
            "appropriate_for": ["public research", "provenance review", "methodology inspection", "evidence packet verification"],
            "not_for": ["emergency response", "automated eligibility decisions", "professional certification", "cryptographic identity proof"],
        },
    }


def verification_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": VERIFICATION_SCHEMA,
        "application_version": APP_VERSION,
        "algorithm": INTEGRITY_ALGORITHM,
        "canonicalization": "UTF-8 JSON, sorted object keys, compact separators, arrays preserved in order",
        "maximum_payload_bytes": MAX_VERIFICATION_BYTES,
        "persistence": False,
        "sensitive_fields_rejected": True,
        "meaning": {
            "matched_digest": "The submitted payload canonicalizes to the expected SHA-256 digest.",
            "not_proven": ["factual correctness", "publisher identity", "legal authenticity", "source availability", "absence of omitted context"],
        },
    }


def verify_payload(payload: Any, expected_digest: str | None = None) -> dict[str, Any]:
    if _contains_sensitive_key(payload):
        raise ObservatoryError("Verification payload contains a sensitive or private field name.")
    canonical = canonical_json(payload)
    byte_count = len(canonical.encode("utf-8"))
    if byte_count > MAX_VERIFICATION_BYTES:
        raise ObservatoryError(f"Verification payload exceeds {MAX_VERIFICATION_BYTES} bytes.")
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    normalized_expected = str(expected_digest or "").strip().lower()
    if normalized_expected and not re.fullmatch(r"[0-9a-f]{64}", normalized_expected):
        raise ObservatoryError("expected_digest must be a 64-character lowercase or uppercase SHA-256 hex digest.")
    return {
        "ok": True,
        "schema": VERIFICATION_SCHEMA,
        "application_version": APP_VERSION,
        "algorithm": INTEGRITY_ALGORITHM,
        "digest": digest,
        "expected_digest": normalized_expected or None,
        "matched": digest == normalized_expected if normalized_expected else None,
        "canonical_bytes": byte_count,
        "persisted": False,
        "boundary": "Digest matching detects payload changes; it does not establish truth, authority, or identity.",
    }


def release_ledger() -> dict[str, Any]:
    core = {
        "schema": "sc-public-release-ledger/2.0",
        "application_version": APP_VERSION,
        "entries": RELEASE_LEDGER,
    }
    return {
        "ok": True,
        **core,
        "generated_at": _utc_now(),
        "integrity": {"algorithm": INTEGRITY_ALGORITHM, "digest": integrity_digest(core)},
    }


def audit_packet() -> dict[str, Any]:
    profile = observatory_profile()
    catalog = audit_catalog()
    lineage = lineage_graph()
    ledger = release_ledger()
    core = {
        "schema": AUDIT_PACKET_SCHEMA,
        "application_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "profile": {
            "release": profile["release"],
            "release_status": profile["release_status"],
            "positioning": profile["positioning"],
            "principles": profile["principles"],
            "counts": profile["counts"],
        },
        "records": catalog["records"],
        "lineage": {
            "schema": lineage["schema"],
            "node_count": len(lineage["nodes"]),
            "edge_count": len(lineage["edges"]),
            "integrity": lineage["integrity"],
        },
        "release_ledger": ledger["entries"],
        "verification": verification_contract(),
    }
    return {
        "ok": True,
        **core,
        "generated_at": _utc_now(),
        "integrity": {
            "algorithm": INTEGRITY_ALGORITHM,
            "digest": integrity_digest(core),
            "scope": "All packet fields except generated_at and integrity",
        },
    }


def audit_packet_markdown() -> str:
    packet = audit_packet()
    lines = [
        "# Sustainable Catalyst Site Intelligence",
        "",
        f"**Release:** v{APP_VERSION} — {RELEASE_NAME}",
        "",
        packet["profile"]["positioning"],
        "",
        "## Audit capabilities",
        "",
    ]
    for principle in packet["profile"]["principles"]:
        lines.append(f"- {principle}")
    lines.extend(["", "## Registered audit records", ""])
    for record in packet["records"]:
        lines.extend(
            [
                f"### {record['title']}",
                "",
                f"- ID: `{record['artifact_id']}`",
                f"- Type: {record['artifact_type']}",
                f"- Route: `{record['route']}`",
                f"- Artifact schema: `{record['artifact_schema']}`",
                f"- Verification level: {record['verification_level']}",
                f"- SHA-256: `{record['integrity']['digest']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Verification boundary",
            "",
            "A matching SHA-256 digest can detect changes to the canonicalized record. It does not prove factual correctness, publisher identity, legal authenticity, or completeness.",
            "",
            f"Packet SHA-256: `{packet['integrity']['digest']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def observatory_diagnostics() -> dict[str, Any]:
    root = _repo_root()
    html = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (root / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    main = (root / "backend/app/main.py").read_text(encoding="utf-8")
    checks = {
        "backend_version": f'APP_VERSION = "{APP_VERSION}"' in (root / "backend/app/version.py").read_text(encoding="utf-8"),
        "observatory_navigation": 'data-route="observatory"' in html,
        "observatory_workspace": 'id="auditablePublicObservatory"' in html,
        "observatory_route_loader": "openAuditablePublicObservatory" in js,
        "observatory_styles": "auditable-observatory" in css,
        "observatory_profile_endpoint": '/public/observatory"' in main,
        "observatory_catalog_endpoint": "/public/observatory/catalog" in main,
        "observatory_verify_endpoint": "/public/observatory/verify" in main,
        "observatory_shortcode": "sc_auditable_public_observatory" in php,
        "wordpress_version": f"Version: {APP_VERSION}" in php and f"const VERSION = '{APP_VERSION}';" in php,
        "audit_record_count": len(AUDIT_ARTIFACTS) >= 10,
        "source_cross_references": all(
            source_id in {record["id"] for record in SOURCE_RECORDS}
            for artifact in AUDIT_ARTIFACTS
            for source_id in artifact.get("source_ids", [])
        ),
        "method_cross_references": all(
            method_id in {record["id"] for record in METHODOLOGY_RECORDS}
            for artifact in AUDIT_ARTIFACTS
            for method_id in artifact.get("methodology_ids", [])
        ),
    }
    return {
        "ok": all(checks.values()),
        "schema": OBSERVATORY_SCHEMA,
        "application_version": APP_VERSION,
        "generated_at": _utc_now(),
        "checks": checks,
        "counts": observatory_profile()["counts"],
        "secrets_exposed": False,
        "manual_review_required": [
            "Production endpoint and cache-header verification",
            "Representative audit-packet download and independent digest check",
            "Screen-reader and mobile traversal of the observatory workspace",
            "WordPress migration review for legacy shortcode aliases",
        ],
    }
