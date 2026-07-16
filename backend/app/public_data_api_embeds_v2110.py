"""Public Data API, Embeds, and Institutional Integration for v2.12.0.

The module exposes a versioned, read-only API catalog over existing public Site
Intelligence workspaces. It does not expose provider credentials, raw private
configuration, or unrestricted upstream payloads. Embeds are stateless iframe
manifests; institutional profiles are public presentation metadata only.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlencode

VERSION = "2.12.0"
API_VERSION = "v1"
RELEASE_SCHEMA = "sc-site-intelligence-public-api-integration/1.0"
CATALOG_SCHEMA = "sc-site-intelligence-public-api-catalog/1.0"
EMBED_SCHEMA = "sc-site-intelligence-embed-manifest/1.0"
INSTITUTION_SCHEMA = "sc-site-intelligence-institution-profile/1.0"

WORKSPACES: tuple[dict[str, Any], ...] = (
    {"id":"global","title":"Global Conditions and Live Map Observatory","view":"global","record_endpoint":"/api/public/v1/workspaces/global/records","formats":["json","geojson"],"domains":["weather","earth-observation","events"]},
    {"id":"economics","title":"Economics, Markets, and Sustainability Signals","view":"economics","record_endpoint":"/api/public/v1/workspaces/economics/records","formats":["json","csv"],"domains":["economics","labour","finance","sustainability"]},
    {"id":"law","title":"International Law and Global Governance Observatory","view":"law","record_endpoint":"/api/public/v1/workspaces/law/records","formats":["json","csv"],"domains":["international-law","governance","human-rights"]},
    {"id":"science","title":"Scientific and Earth Systems Observatory","view":"science","record_endpoint":"/api/public/v1/workspaces/science/records","formats":["json","geojson","stac"],"domains":["earth-systems","space","biology","chemistry","materials"]},
    {"id":"humanitarian","title":"Humanitarian, Conflict, and Displacement Observatory","view":"humanitarian","record_endpoint":"/api/public/v1/workspaces/humanitarian/records","formats":["json","csv"],"domains":["humanitarian","conflict","displacement"]},
    {"id":"resources","title":"Trade, Energy, and Resource Security Observatory","view":"resources","record_endpoint":"/api/public/v1/workspaces/resources/records","formats":["json","csv"],"domains":["trade","energy","food","water","materials"]},
    {"id":"dossiers","title":"Unified Country and Regional Intelligence Dossiers","view":"dossiers","record_endpoint":"","formats":["json"],"domains":["cross-domain"],"requires_subject":True},
    {"id":"alerts","title":"Alerts, Monitoring, and Live Intelligence Streams","view":"alerts","record_endpoint":"","formats":["json","event-stream"],"domains":["monitoring"]},
    {"id":"scenarios","title":"Comparative Intelligence and Scenario Studio","view":"scenarios","record_endpoint":"","formats":["json"],"domains":["comparison","scenario"]},
    {"id":"research","title":"Research Paths, Saved Investigations, and Briefing Workflows","view":"research","record_endpoint":"","formats":["json"],"domains":["research-workflow"]},
    {"id":"integration","title":"Public Data API, Embeds, and Institutional Integration","view":"integration","record_endpoint":"","formats":["json","html"],"domains":["integration"]},
    {"id":"experience","title":"Offline, Mobile, Accessibility, and Performance","view":"experience","record_endpoint":"","formats":["json","html"],"domains":["delivery","accessibility","performance"]},
)
WORKSPACE_MAP = {item["id"]: item for item in WORKSPACES}
ALLOWED_THEMES = {"system", "light", "dark"}
ALLOWED_CHROME = {"full", "compact", "none"}
SAFE_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
SENSITIVE_RE = re.compile(r"(?:api[_-]?key|token|secret|password|authorization|cookie|session|private[_-]?url|stack[_-]?trace)", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _text(value: Any, limit: int = 500) -> str:
    return " ".join(re.sub(r"[\x00-\x1f]", "", str(value or "")).split())[:limit]


def _url(value: Any) -> str:
    text = _text(value, 1200)
    if not text.lower().startswith(("https://", "http://")):
        return ""
    if re.search(r"(?:api[_-]?key|access[_-]?token|token|authorization)=", text, re.I):
        return text.split("?", 1)[0]
    return text


def _safe(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return None
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, child in value.items():
            if SENSITIVE_RE.search(str(key)):
                continue
            cleaned = _safe(child, depth + 1)
            if cleaned is not None:
                out[str(key)[:120]] = cleaned
        return out
    if isinstance(value, list):
        return [_safe(item, depth + 1) for item in value[:500]]
    if isinstance(value, str):
        return _url(value) if value.lower().startswith(("https://", "http://")) else value[:5000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _text(value, 1000)


def integration_config(settings: Any = None) -> dict[str, Any]:
    get = lambda attr, env, default: getattr(settings, attr, None) if getattr(settings, attr, None) is not None else os.getenv(env, default)
    allowed_origins = [part.strip() for part in str(get("public_embed_allowed_origins", "SC_SI_PUBLIC_EMBED_ALLOWED_ORIGINS", "")).split(",") if part.strip()]
    return {
        "enabled": _bool(get("public_data_api_enabled", "SC_SI_PUBLIC_DATA_API_ENABLED", "true"), True),
        "embeds_enabled": _bool(get("public_embeds_enabled", "SC_SI_PUBLIC_EMBEDS_ENABLED", "true"), True),
        "max_limit": max(10, min(int(get("public_data_api_max_limit", "SC_SI_PUBLIC_DATA_API_MAX_LIMIT", 200)), 500)),
        "allowed_origins": allowed_origins,
        "institution_name": _text(get("institution_name", "SC_SI_INSTITUTION_NAME", "Sustainable Catalyst"), 180),
        "institution_website": _url(get("institution_website", "SC_SI_INSTITUTION_WEBSITE", "https://sustainablecatalyst.com")),
        "institution_logo_url": _url(get("institution_logo_url", "SC_SI_INSTITUTION_LOGO_URL", "")),
        "institution_contact": _text(get("institution_contact", "SC_SI_INSTITUTION_CONTACT", ""), 240),
        "institution_accent": str(get("institution_accent", "SC_SI_INSTITUTION_ACCENT", "#8b1e3f")),
    }


def build_overview(settings: Any = None) -> dict[str, Any]:
    cfg = integration_config(settings)
    return {
        "ok": True,
        "schema": RELEASE_SCHEMA,
        "version": VERSION,
        "api_version": API_VERSION,
        "release_name": "Public Data API, Embeds, and Institutional Integration",
        "generated_at": _now(),
        "integration": {"state": "ready" if cfg["enabled"] else "disabled", "read_only": True, "credential_exposed": False, "server_user_tracking": False},
        "capabilities": ["versioned public read API", "workspace catalog", "sanitized record access", "embed manifest generator", "institutional presentation profile", "CSV, GeoJSON, STAC, and JSON discovery"],
        "responsible_use": ["Public API responses preserve source and methodological context.", "Institutional branding does not change evidence or source attribution.", "Embeds are read-only public views and do not expose provider credentials."],
        "links": {"root": "/api/public/v1", "catalog": "/api/public/v1/catalog", "integration_workspace": "/app/?view=integration"},
    }


def build_catalog(settings: Any = None) -> dict[str, Any]:
    cfg = integration_config(settings)
    items = []
    for item in WORKSPACES:
        row = dict(item)
        row["app_url"] = f"/app/?{urlencode({'view': item['view']})}"
        row["manifest_url"] = f"/api/public/v1/workspaces/{item['id']}"
        items.append(row)
    return {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "api_version": API_VERSION,
        "generated_at": _now(),
        "count": len(items),
        "workspaces": items,
        "limits": {"default": min(100, cfg["max_limit"]), "maximum": cfg["max_limit"]},
        "formats": ["application/json", "text/csv", "application/geo+json", "application/vnd.api+json", "text/event-stream"],
        "license_note": "Each record retains its original source, license, attribution, and reuse context.",
    }


def build_workspace_manifest(workspace_id: str, settings: Any = None) -> dict[str, Any]:
    item = WORKSPACE_MAP.get(_text(workspace_id, 80).lower())
    if not item:
        raise ValueError("Unknown public workspace.")
    cfg = integration_config(settings)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-public-workspace/1.0",
        "version": VERSION,
        **dict(item),
        "app_url": f"/app/?{urlencode({'view': item['view']})}",
        "embed_url": build_embed_manifest(item["view"], settings=settings)["url"],
        "limits": {"maximum_records": cfg["max_limit"]},
        "authentication": "none for public read endpoints",
        "credential_exposed": False,
    }


def _dispatch_records(workspace_id: str, settings: Any, params: Mapping[str, Any]) -> dict[str, Any]:
    limit = max(1, min(int(params.get("limit") or 100), integration_config(settings)["max_limit"]))
    query = _text(params.get("query"), 240)
    country = _text(params.get("country") or params.get("geography_code"), 20).upper()
    source_id = _text(params.get("source_id"), 180)
    if workspace_id == "global":
        from .global_conditions_observatory import build_global_conditions_features
        return build_global_conditions_features(settings, bbox=_text(params.get("bbox"), 120), domain=_text(params.get("domain"), 100), source_id=source_id, limit=limit)
    if workspace_id == "economics":
        from .economics_markets_sustainability import build_economic_records
        return build_economic_records(settings, geography_code=country, source_id=source_id, query=query, limit=limit, offset=max(0, int(params.get("offset") or 0)))
    if workspace_id == "law":
        from .international_law_observatory import build_law_records
        payload = build_law_records(settings, country=country, query=query, authority_level=_text(params.get("authority_level"), 100), record_type=_text(params.get("record_type"), 100), limit=limit, offset=max(0, int(params.get("offset") or 0)))
        if source_id:
            payload["records"] = [row for row in payload.get("records", []) if str(row.get("source_id") or "") == source_id]
            payload["pagination"]["returned"] = len(payload["records"])
        return payload
    if workspace_id == "science":
        from .scientific_earth_systems_observatory import build_science_records
        payload = build_science_records(settings, source_id=source_id, query=query, discipline=_text(params.get("discipline"), 100), limit=limit, offset=max(0, int(params.get("offset") or 0)))
        family = _text(params.get("family"), 100).lower()
        if family:
            payload["records"] = [row for row in payload.get("records", []) if str(row.get("family") or "").lower() == family]
            payload["total"] = len(payload["records"])
        return payload
    if workspace_id == "humanitarian":
        from .humanitarian_conflict_displacement_observatory import build_records
        return build_records(settings, country=country, source_id=source_id, query=query, category=_text(params.get("category"), 100), limit=limit, offset=max(0, int(params.get("offset") or 0)))
    if workspace_id == "resources":
        from .trade_energy_resource_security_observatory import build_records
        return build_records(settings, geography_code=country, source_id=source_id, query=query, family=_text(params.get("family"), 100), indicator_code=_text(params.get("indicator_code"), 160), limit=limit, offset=max(0, int(params.get("offset") or 0)))
    raise ValueError("This workspace exposes a specialized workflow rather than a generic records endpoint.")


def build_workspace_records(workspace_id: str, settings: Any = None, **params: Any) -> dict[str, Any]:
    cfg = integration_config(settings)
    if not cfg["enabled"]:
        raise ValueError("Public Data API is disabled.")
    workspace_id = _text(workspace_id, 80).lower()
    item = WORKSPACE_MAP.get(workspace_id)
    if not item:
        raise ValueError("Unknown public workspace.")
    if not item.get("record_endpoint"):
        raise ValueError("This workspace does not expose a generic records collection.")
    payload = _safe(_dispatch_records(workspace_id, settings, params))
    return {
        "ok": True,
        "schema": "sc-site-intelligence-public-record-collection/1.0",
        "version": VERSION,
        "workspace": workspace_id,
        "generated_at": _now(),
        "credential_exposed": False,
        "payload": payload,
    }


def build_embed_manifest(view: str = "overview", *, theme: str = "system", chrome: str = "compact", height: int = 900, institution: str = "", settings: Any = None) -> dict[str, Any]:
    cfg = integration_config(settings)
    if not cfg["embeds_enabled"]:
        raise ValueError("Public embeds are disabled.")
    view = _text(view, 80).lower() or "overview"
    allowed_views = {item["view"] for item in WORKSPACES} | {"overview", "earth", "country", "events", "compare", "thematic", "briefing", "sources", "saved", "observatory", "launch"}
    if view not in allowed_views:
        raise ValueError("Unknown embed view.")
    theme = theme if theme in ALLOWED_THEMES else "system"
    chrome = chrome if chrome in ALLOWED_CHROME else "compact"
    height = max(420, min(int(height), 2200))
    query = {"view": view, "embed": "1", "theme": theme, "chrome": chrome}
    if institution:
        query["institution"] = _text(institution, 120)
    url = f"/app/?{urlencode(query)}"
    return {
        "ok": True,
        "schema": EMBED_SCHEMA,
        "version": VERSION,
        "view": view,
        "theme": theme,
        "chrome": chrome,
        "height": height,
        "url": url,
        "iframe": f'<iframe title="Sustainable Catalyst Site Intelligence — {view}" src="{url}" style="width:100%;height:{height}px;border:0" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write"></iframe>',
        "allowed_origins": cfg["allowed_origins"],
        "credential_exposed": False,
        "tracking": "No Site Intelligence user profile is created by the embed manifest.",
    }


def build_institution_profile(settings: Any = None) -> dict[str, Any]:
    cfg = integration_config(settings)
    accent = cfg["institution_accent"] if SAFE_COLOR.match(cfg["institution_accent"]) else "#8b1e3f"
    return {
        "ok": True,
        "schema": INSTITUTION_SCHEMA,
        "version": VERSION,
        "name": cfg["institution_name"],
        "website": cfg["institution_website"],
        "logo_url": cfg["institution_logo_url"],
        "contact": cfg["institution_contact"],
        "accent": accent,
        "attribution_required": True,
        "evidence_ownership": "Original providers retain ownership and license terms for their data.",
        "branding_scope": "Presentation metadata only; source attribution, methodology, and record content are unchanged.",
    }


def build_openapi_summary(settings: Any = None) -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-site-intelligence-openapi-summary/1.0",
        "version": VERSION,
        "base_path": "/api/public/v1",
        "authentication": "No authentication for published read endpoints.",
        "endpoints": [
            {"method":"GET","path":"/api/public/v1","purpose":"API overview"},
            {"method":"GET","path":"/api/public/v1/catalog","purpose":"Workspace and format catalog"},
            {"method":"GET","path":"/api/public/v1/workspaces/{workspace_id}","purpose":"Workspace manifest"},
            {"method":"GET","path":"/api/public/v1/workspaces/{workspace_id}/records","purpose":"Sanitized public records for supported workspaces"},
            {"method":"GET","path":"/api/public/v1/workspaces/{workspace_id}/records.csv","purpose":"Bounded source-preserving CSV export"},
            {"method":"GET","path":"/api/public/v1/embed","purpose":"Read-only iframe manifest"},
            {"method":"GET","path":"/api/public/v1/institution","purpose":"Public institutional presentation metadata"},
            {"method":"GET","path":"/api/public/v1/diagnostics","purpose":"Public integration capabilities"},
        ],
        "documentation": {"interactive": "/docs", "schema": "/openapi.json"},
        "limits": build_catalog(settings)["limits"],
    }


def build_diagnostics(settings: Any = None) -> dict[str, Any]:
    cfg = integration_config(settings)
    return {
        "ok": True,
        "schema": "sc-site-intelligence-public-api-diagnostics/1.0",
        "version": VERSION,
        "enabled": cfg["enabled"],
        "embeds_enabled": cfg["embeds_enabled"],
        "workspace_count": len(WORKSPACES),
        "generic_record_workspaces": [item["id"] for item in WORKSPACES if item.get("record_endpoint")],
        "allowed_origin_count": len(cfg["allowed_origins"]),
        "credential_exposed": False,
        "server_user_tracking": False,
        "paid_dependency_required": False,
    }


def build_workspace_csv(workspace_id: str, settings: Any = None, **params: Any) -> str:
    """Return a bounded, source-preserving CSV representation of public records."""
    import csv
    import io
    import json
    collection = build_workspace_records(workspace_id, settings, **params)
    payload = collection.get("payload") or {}
    rows = payload.get("records") if isinstance(payload, Mapping) else []
    if not isinstance(rows, list) and isinstance(payload, Mapping) and payload.get("type") == "FeatureCollection":
        rows = []
        for feature in payload.get("features") or []:
            if not isinstance(feature, Mapping):
                continue
            row = dict(feature.get("properties") or {})
            row["feature_id"] = feature.get("id") or ""
            row["geometry"] = json.dumps(feature.get("geometry"), sort_keys=True, separators=(",", ":"))
            rows.append(row)
    rows = [row for row in (rows or []) if isinstance(row, Mapping)]
    columns: list[str] = []
    for row in rows[:500]:
        for key in row.keys():
            if not SENSITIVE_RE.search(str(key)) and str(key) not in columns:
                columns.append(str(key))
    preferred = ["id", "title", "source_id", "source_url", "geography_code", "country", "period", "observed_at", "published_at", "value_number", "value_text", "unit", "license", "attribution"]
    columns = [key for key in preferred if key in columns] + [key for key in columns if key not in preferred]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns or ["message"], extrasaction="ignore")
    writer.writeheader()
    if not rows:
        writer.writerow({(columns or ["message"])[0]: "No public records returned for the selected query."})
    for row in rows:
        flat: dict[str, Any] = {}
        for key in columns:
            value = _safe(row.get(key))
            flat[key] = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value
        writer.writerow(flat)
    return output.getvalue()
