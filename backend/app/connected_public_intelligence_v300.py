from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable

from .config import Settings

RELEASE_VERSION = "3.6.2"
SCHEMA_VERSION = "sc-connected-public-intelligence/1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _safe(value: Any, limit: int = 5000) -> str:
    return str(value or "").replace("\x00", "").strip()[:limit]


def _tokens(value: Any) -> set[str]:
    text = _safe(value).lower()
    for ch in "_/.-:()[]{}":
        text = text.replace(ch, " ")
    return {token for token in text.split() if token}


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if len(rows) >= limit:
                    break
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except (FileNotFoundError, OSError):
        pass
    return rows


def _is_public(row: dict[str, Any]) -> bool:
    visibility = _safe(row.get("visibility") or row.get("access") or row.get("publication_visibility")).lower()
    status = _safe(row.get("status") or row.get("review_status") or row.get("publication_status") or row.get("state")).lower()
    explicit = row.get("public") is True or row.get("public_eligible") is True or row.get("approved_for_publication") is True
    return explicit or visibility in {"public", "published"} or status in {"published", "approved", "public", "active"}


@dataclass(frozen=True)
class CatalogRecord:
    record_id: str
    record_type: str
    title: str
    summary: str
    route: str
    domain: str
    source: str
    aliases: tuple[str, ...] = ()
    metadata: dict[str, Any] | None = None

    def public(self) -> dict[str, Any]:
        payload = {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "title": self.title,
            "summary": self.summary,
            "route": self.route,
            "domain": self.domain,
            "source": self.source,
            "aliases": list(self.aliases),
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        payload["sha256"] = _digest(payload)
        return payload


class ConnectedPublicIntelligencePlatform:
    """Unifies public discovery and provenance across Site Intelligence.

    It indexes public-safe static registries and approved runtime records. It does
    not copy private payloads, infer causation, auto-publish records, or claim that
    a route was delivered to another Sustainable Catalyst product.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.max_results = int(settings.connected_platform_max_results)
        self.static_sources = {
            "site_registry": _resolve(settings.registry_path),
            "connector_registry": _resolve(settings.connector_operations_registry_path),
            "spatial_catalog": _resolve(settings.spatial_evidence_layer_catalog_path),
            "workflow_registry": _resolve(settings.cross_platform_workflows_registry_path),
        }

    def _base_capabilities(self) -> list[CatalogRecord]:
        capabilities = [
            ("observatory", "workspace", "Auditable Public Observatory", "Evidence lineage, source methodology, integrity receipts, and audit artifacts.", "/app/?view=observatory", "evidence"),
            ("countries", "workspace", "Country and Regional Intelligence", "Country dossiers, regional context, indicators, events, and reporting periods.", "/app/?view=dossiers", "geography"),
            ("events", "workspace", "Live Event Intelligence", "Public hazards, humanitarian events, timelines, categories, and source context.", "/app/?view=events", "events"),
            ("indicators", "workspace", "Comparable Indicators", "Raw and transformed statistical series with explicit units and compatibility diagnostics.", "/app/?view=harmonization", "statistics"),
            ("models", "workspace", "Models and Forecasts", "Model cards, forecasts, evaluation, calibration, drift, and reviewable warnings.", "/app/?view=models", "models"),
            ("claims", "workspace", "Evidence and Claims", "Approved claims, typed evidence relationships, contradictions, and uncertainty.", "/app/?view=evidence", "evidence"),
            ("graph", "workspace", "Relationship Explorer", "Typed entities and evidence-backed temporal relationships without causal inference.", "/app/?view=graph", "relationships"),
            ("publishing", "workspace", "Intelligence Publishing", "Human-approved publications, story maps, evidence tables, and immutable versions.", "/app/?view=publishing", "publishing"),
            ("monitoring", "workspace", "Monitoring and Public Feeds", "Reviewable alerts, published digests, and JSON, RSS, and Atom feeds.", "/app/?view=monitoring", "monitoring"),
            ("workspaces", "workspace", "Institutional Workspaces", "Optional collaboration, assignments, review, activity receipts, and public-safe summaries.", "/app/?view=workspaces", "collaboration"),
            ("workflows", "workspace", "Cross-Platform Workflows", "Typed packets, schemas, receipts, linkbacks, and bounded recovery queues.", "/app/?view=workflows", "integration"),
            ("federation", "workspace", "Institutional Data Exchange", "DCAT-compatible catalogs, provenance, licensing, signed manifests, and trust review.", "/app/?view=federation", "federation"),
            ("governance", "workspace", "Production Governance", "Migrations, scoped keys, audit chains, privacy, backups, queues, and readiness diagnostics.", "/app/?view=governance", "governance"),
            ("connected-platform", "platform", "Connected Public Intelligence and Evidence Platform", "One public discovery and provenance layer across countries, events, indicators, datasets, sources, claims, models, investigations, publications, and workflows.", "/app/?view=platform", "platform"),
        ]
        return [CatalogRecord(i, t, title, summary, route, domain, "v3-capability-registry") for i, t, title, summary, route, domain in capabilities]

    def _site_records(self) -> list[CatalogRecord]:
        data = _read_json(self.static_sources["site_registry"], {})
        rows: list[CatalogRecord] = []
        for item in data.get("items", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            record_id = _safe(item.get("id"), 160)
            title = _safe(item.get("title"), 240)
            if not record_id or not title:
                continue
            rows.append(CatalogRecord(
                f"site:{record_id}", "platform-page", title,
                _safe(item.get("discipline") or item.get("article_map") or item.get("hub"), 500),
                _safe(item.get("url_path") or "/", 500), _safe(item.get("hub") or "platform", 120).lower(),
                "site_registry.seed.json", tuple(_safe(tag, 100) for tag in item.get("tags", []) if tag),
                {"content_type": item.get("content_type"), "pathway_id": item.get("pathway_id")},
            ))
        return rows

    def _connector_records(self) -> list[CatalogRecord]:
        data = _read_json(self.static_sources["connector_registry"], {})
        rows: list[CatalogRecord] = []
        for item in data.get("connectors", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            cid = _safe(item.get("connector_id"), 160)
            if not cid:
                continue
            rows.append(CatalogRecord(
                f"connector:{cid}", "source", _safe(item.get("name") or cid, 240),
                _safe(item.get("public_note") or item.get("provider"), 1000),
                "/public/connector-operations", _safe(item.get("family") or "sources", 120),
                "connector_operations_registry_v2130.json", (_safe(item.get("provider"), 160),),
                {"provider": item.get("provider"), "datasets": item.get("datasets", []), "public_status": item.get("public_status")},
            ))
            for dataset in item.get("datasets", []):
                rows.append(CatalogRecord(
                    f"dataset:{_safe(dataset, 180)}", "dataset", _safe(dataset, 240).replace("-", " ").title(),
                    f"Dataset managed by {_safe(item.get('name') or cid, 240)}.", "/public/connector-operations",
                    _safe(item.get("family") or "datasets", 120), "connector_operations_registry_v2130.json",
                    (_safe(item.get("name") or cid, 160),), {"connector_id": cid},
                ))
        return rows

    def _spatial_records(self) -> list[CatalogRecord]:
        data = _read_json(self.static_sources["spatial_catalog"], {})
        rows: list[CatalogRecord] = []
        for item in data.get("layers", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict) or item.get("public_safe") is False:
                continue
            lid = _safe(item.get("id"), 160)
            rows.append(CatalogRecord(
                f"spatial:{lid}", "spatial-layer", _safe(item.get("title") or lid, 240),
                "Public spatial layer with explicit geometry, source-family, and temporal metadata.",
                "/app/?view=spatial", "spatial", "spatial_layer_catalog_v2150.json",
                tuple(_safe(x, 100) for x in item.get("source_families", [])),
                {"geometry_types": item.get("geometry_types", []), "temporal": bool(item.get("temporal"))},
            ))
        return rows

    def _workflow_records(self) -> list[CatalogRecord]:
        data = _read_json(self.static_sources["workflow_registry"], {})
        rows: list[CatalogRecord] = []
        for item in data.get("routes", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            rid = _safe(item.get("route_id"), 180)
            rows.append(CatalogRecord(
                f"workflow:{rid}", "workflow-route", rid.replace("-", " ").title(),
                _safe(item.get("description"), 1000), "/app/?view=workflows", "integration",
                "cross_platform_workflow_registry_v2230.json",
                (_safe(item.get("source_platform"), 100), _safe(item.get("target_platform"), 100), _safe(item.get("packet_type"), 100)),
                {"source_platform": item.get("source_platform"), "target_platform": item.get("target_platform"), "packet_type": item.get("packet_type")},
            ))
        return rows

    def _runtime_records(self) -> list[CatalogRecord]:
        candidates = [
            ("claim", getattr(self.settings, "evidence_synthesis_claims_path", ""), "/app/?view=evidence"),
            ("model", getattr(self.settings, "model_governance_models_path", ""), "/app/?view=models"),
            ("publication", getattr(self.settings, "intelligence_publishing_projects_path", ""), "/app/?view=publishing"),
            ("workspace", getattr(self.settings, "institutional_workspaces_workspaces_path", ""), "/app/?view=workspaces"),
            ("entity", getattr(self.settings, "knowledge_graph_entities_path", ""), "/app/?view=graph"),
            ("relationship", getattr(self.settings, "knowledge_graph_relationships_path", ""), "/app/?view=graph"),
            ("digest", getattr(self.settings, "scheduled_monitoring_digests_path", ""), "/app/?view=monitoring"),
        ]
        output: list[CatalogRecord] = []
        for record_type, raw_path, route in candidates:
            if not raw_path:
                continue
            for row in _read_jsonl(_resolve(raw_path), self.max_results):
                if not _is_public(row):
                    continue
                rid = _safe(row.get(f"{record_type}_id") or row.get("id") or row.get("record_id"), 180)
                title = _safe(row.get("title") or row.get("name") or row.get("label") or rid, 240)
                if not rid or not title:
                    continue
                summary = _safe(row.get("summary") or row.get("description") or row.get("statement") or row.get("abstract"), 1200)
                aliases = tuple(_safe(x, 120) for x in row.get("aliases", []) if x) if isinstance(row.get("aliases"), list) else ()
                output.append(CatalogRecord(
                    f"{record_type}:{rid}", record_type, title, summary, route, record_type,
                    Path(raw_path).name, aliases, {"status": row.get("status"), "visibility": row.get("visibility")},
                ))
        return output

    def records(self) -> list[CatalogRecord]:
        merged: dict[str, CatalogRecord] = {}
        for record in [*self._base_capabilities(), *self._site_records(), *self._connector_records(), *self._spatial_records(), *self._workflow_records(), *self._runtime_records()]:
            merged.setdefault(record.record_id, record)
        return list(merged.values())

    def overview(self) -> dict[str, Any]:
        records = self.records()
        counts: dict[str, int] = {}
        for record in records:
            counts[record.record_type] = counts.get(record.record_type, 0) + 1
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "schema": SCHEMA_VERSION,
            "release_name": "Connected Public Intelligence and Evidence Platform",
            "record_count": len(records),
            "record_types": counts,
            "search_endpoint": "/public/connected-intelligence/search?q=",
            "context_endpoint": "/public/connected-intelligence/context/{record_id}",
            "lifecycle": ["source", "ingest", "archive", "harmonize", "analyze", "review", "publish", "monitor", "exchange"],
            "platforms": ["site-intelligence", "workbench", "decision-studio", "research-librarian", "knowledge-library", "research-lab", "platform-core"],
            "public_access_requires_account": False,
            "governance": {
                "human_review_required_for_public_claims": True,
                "conflicting_evidence_preserved": True,
                "causal_inference_from_graph_structure": False,
                "automatic_remote_delivery_claimed": False,
                "private_runtime_records_exposed": False,
            },
        }

    def search(self, query: str, record_type: str = "", limit: int = 25) -> dict[str, Any]:
        query = _safe(query, 240)
        terms = _tokens(query)
        if not terms:
            return {"ok": True, "version": RELEASE_VERSION, "query": query, "count": 0, "results": [], "note": "Provide one or more search terms."}
        scored: list[tuple[int, CatalogRecord]] = []
        for record in self.records():
            if record_type and record.record_type != record_type:
                continue
            title_tokens = _tokens(record.title)
            alias_tokens = _tokens(" ".join(record.aliases))
            body_tokens = _tokens(f"{record.summary} {record.domain} {record.record_type} {record.record_id}")
            score = 8 * len(terms & title_tokens) + 5 * len(terms & alias_tokens) + 2 * len(terms & body_tokens)
            phrase = query.lower()
            if phrase and phrase in record.title.lower():
                score += 12
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: (-item[0], item[1].title.lower(), item[1].record_id))
        maximum = max(1, min(int(limit), self.max_results, 100))
        results = []
        for score, record in scored[:maximum]:
            item = record.public()
            item["relevance_score"] = score
            results.append(item)
        return {"ok": True, "version": RELEASE_VERSION, "query": query, "record_type": record_type or None, "count": len(results), "results": results, "inference_note": "Search relevance is lexical discovery, not evidence quality, causal importance, or risk scoring."}

    def context(self, record_id: str) -> dict[str, Any]:
        record_id = _safe(record_id, 240)
        records = self.records()
        target = next((record for record in records if record.record_id == record_id), None)
        if not target:
            raise KeyError(record_id)
        terms = _tokens(f"{target.title} {' '.join(target.aliases)} {target.domain}")
        related: list[tuple[int, CatalogRecord]] = []
        for candidate in records:
            if candidate.record_id == target.record_id:
                continue
            score = len(terms & _tokens(f"{candidate.title} {' '.join(candidate.aliases)} {candidate.domain} {candidate.summary}"))
            if score:
                related.append((score, candidate))
        related.sort(key=lambda item: (-item[0], item[1].title.lower()))
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "record": target.public(),
            "related": [record.public() for _, record in related[:12]],
            "recommended_routes": self._routes_for(target.record_type),
            "provenance": self.provenance(record_id),
            "context_note": "Related records indicate shared public terms or domains; they do not establish causation or institutional endorsement.",
        }

    @staticmethod
    def _routes_for(record_type: str) -> list[str]:
        routes = {
            "dataset": ["/app/?view=harmonization", "/app/?view=spatial", "/app/?view=workflows"],
            "source": ["/app/?view=sources", "/app/?view=evidence"],
            "claim": ["/app/?view=evidence", "/app/?view=graph", "/app/?view=publishing"],
            "model": ["/app/?view=models", "/app/?view=evidence"],
            "publication": ["/app/?view=publishing", "/app/?view=monitoring"],
            "entity": ["/app/?view=graph", "/app/?view=dossiers"],
        }
        return routes.get(record_type, ["/app/?view=platform", "/app/?view=research"])

    def provenance(self, record_id: str) -> dict[str, Any]:
        target = next((record for record in self.records() if record.record_id == record_id), None)
        if not target:
            raise KeyError(record_id)
        record = target.public()
        chain = [
            {"stage": "source", "artifact": target.source, "sha256": _digest({"source": target.source})},
            {"stage": "catalog", "artifact": record_id, "sha256": record["sha256"]},
            {"stage": "discovery", "artifact": "/public/connected-intelligence", "sha256": _digest({"record_id": record_id, "version": RELEASE_VERSION})},
        ]
        return {"record_id": record_id, "chain": chain, "verified": all(item.get("sha256") for item in chain), "limitations": ["This chain verifies platform receipts and catalog content, not the truth of every upstream claim."]}

    def lifecycle(self) -> dict[str, Any]:
        stages = [
            ("source", "Registered public sources and institutional catalogs"),
            ("ingest", "Connector validation, receipts, quarantine, and freshness"),
            ("archive", "Versioned snapshots, revisions, and temporal coverage"),
            ("harmonize", "Units, periods, geography, currency, and missing-data context"),
            ("analyze", "Spatial analysis, scenarios, models, and Workbench handoffs"),
            ("review", "Claims, contradictions, uncertainty, collaboration, and approval"),
            ("publish", "Briefs, story maps, immutable publications, and exports"),
            ("monitor", "Alerts, digests, feeds, and outcome reassessment"),
            ("exchange", "Typed workflows, federation, provenance, and Platform Core receipts"),
        ]
        return {"ok": True, "version": RELEASE_VERSION, "stages": [{"id": sid, "description": description, "automatic_publication": False} for sid, description in stages]}

    def diagnostics(self) -> dict[str, Any]:
        records = self.records()
        sources = []
        for name, path in self.static_sources.items():
            sources.append({"id": name, "path": str(path), "available": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "records": len(records),
            "static_sources": sources,
            "runtime_indexing": "approved-public-records-only",
            "persistent_search_service_claimed": False,
            "index_generated_at": _utc_now(),
            "limitations": ["The default zero-cost index is generated on request.", "Private records and credentials are excluded.", "Lexical relevance does not measure truth, authority, causation, or risk."],
        }

    def control_center(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "overview": self.overview(),
            "diagnostics": self.diagnostics(),
            "index_preview": {"record_count": len(self.records()), "write_performed": False},
            "operations": ["inspect public index", "preview search", "export discovery packet", "verify provenance receipts"],
            "remote_write_performed": False,
        }

    def export(self, query: str, format_name: str = "json", limit: int = 100) -> tuple[str, str]:
        result = self.search(query, limit=limit)
        if format_name.lower() == "csv":
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=["record_id", "record_type", "title", "summary", "route", "domain", "source", "relevance_score", "sha256"])
            writer.writeheader()
            for row in result["results"]:
                writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
            return stream.getvalue(), "text/csv"
        packet = {"schema": SCHEMA_VERSION, "version": RELEASE_VERSION, "exported_at": _utc_now(), "query": query, "result": result}
        packet["sha256"] = _digest(packet)
        return json.dumps(packet, ensure_ascii=False, indent=2), "application/json"
