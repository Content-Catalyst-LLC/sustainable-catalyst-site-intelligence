"""Public-safe homepage summary for Site Intelligence v4.40.0.3.

The homepage capability strip is deliberately distinct from the bounded signal
refresh.  Capability counts describe registered product coverage; signal counts
describe only the current refresh and are exposed separately.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .version import APP_VERSION


SCHEMA_VERSION = "sc-site-intelligence-home-summary/1.1"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
COUNTRY_REGISTRY = DATA_DIR / "country_identity_registry_v43523.json"
CONNECTOR_REGISTRY = DATA_DIR / "connector_operations_registry_v2130.json"
PLATFORM_POLICY = DATA_DIR / "unified_public_intelligence_policy_v4000.json"
LIVE_SOURCE_REGISTRY = DATA_DIR / "live_intelligence_source_registry_v320.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _bounded_text(value: Any, limit: int = 180) -> str:
    return " ".join(str(value or "").split())[:limit]


def _country_count() -> int:
    registry = _read_json(COUNTRY_REGISTRY)
    countries = registry.get("countries")
    observed = len(countries) if isinstance(countries, list) else 0
    declared = registry.get("country_count")
    return observed if observed else max(0, int(declared or 0))


def _enabled_connector_count() -> int:
    registry = _read_json(CONNECTOR_REGISTRY)
    connectors = registry.get("connectors") if isinstance(registry.get("connectors"), list) else []
    return sum(1 for connector in connectors if isinstance(connector, Mapping) and connector.get("enabled") is True)


def _public_workspace_count() -> int:
    policy = _read_json(PLATFORM_POLICY)
    routes: list[str] = []
    areas = policy.get("primary_areas") if isinstance(policy.get("primary_areas"), list) else []
    for area in areas:
        if not isinstance(area, Mapping):
            continue
        for route in area.get("routes") or []:
            route_id = str(route or "").strip()
            if route_id:
                routes.append(route_id)
    unique_routes = len(set(routes))
    if unique_routes:
        return unique_routes
    compatibility = policy.get("compatibility") if isinstance(policy.get("compatibility"), Mapping) else {}
    return max(0, int(compatibility.get("legacy_route_count") or 0))


def _live_feed_count() -> int:
    registry = _read_json(LIVE_SOURCE_REGISTRY)
    sources = registry.get("sources") if isinstance(registry.get("sources"), list) else []
    return len([source for source in sources if isinstance(source, Mapping)])


def _highlight(signal: Mapping[str, Any]) -> dict[str, Any]:
    primary = signal.get("primary_destination") if isinstance(signal.get("primary_destination"), Mapping) else {}
    return {
        "signal_id": _bounded_text(signal.get("signal_id"), 180),
        "category": _bounded_text(signal.get("family_label") or signal.get("category_label") or signal.get("category"), 80),
        "label": _bounded_text(signal.get("short_label") or signal.get("label"), 100),
        "value": _bounded_text(signal.get("formatted_value") or signal.get("value"), 180),
        "source": _bounded_text(signal.get("source_name") or signal.get("source_label") or signal.get("feed_id"), 120),
        "freshness_state": _bounded_text(signal.get("freshness_state") or "unknown", 40),
        "href": _bounded_text(primary.get("url") or signal.get("context_view_url") or "/app/?view=overview", 500),
    }


def build_homepage_summary(
    live_payload: Mapping[str, Any] | None = None,
    *,
    live_feed_count: int | None = None,
) -> dict[str, Any]:
    """Build the homepage snapshot without conflating capability and refresh counts."""
    payload = dict(live_payload or {})
    signals = [signal for signal in (payload.get("signals") or []) if isinstance(signal, Mapping)]
    country_count = _country_count()
    enabled_connector_count = _enabled_connector_count()
    public_workspace_count = _public_workspace_count()
    governed_live_feed_count = _live_feed_count() if live_feed_count is None else max(0, int(live_feed_count))
    gateway = payload.get("gateway") if isinstance(payload.get("gateway"), Mapping) else {}
    represented_source_count = max(0, int(gateway.get("represented_source_count") or 0))
    generated_at = _bounded_text(payload.get("generated_at"), 80)
    featured_signal_count = len(signals)

    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "title": "Site Intelligence",
        "summary": "Explore geographic, environmental, humanitarian, scientific, and institutional evidence through a provenance-aware public intelligence system.",
        "status": {
            "state": "online",
            "label": "Site Intelligence Online",
            "delivery_state": "live" if featured_signal_count else "available",
            "message": "Current public signals are available." if featured_signal_count else "The platform is available; no current signals were returned for this refresh.",
        },
        "metrics": [
            {"id": "country_profiles", "value": country_count, "label": "country profiles", "basis": "first-party country identity registry"},
            {"id": "enabled_connectors", "value": enabled_connector_count, "label": "enabled connectors", "basis": "connector operations registry; connector availability and credentials vary"},
            {"id": "public_workspaces", "value": public_workspace_count, "label": "public workspaces", "basis": "registered public intelligence routes across six primary areas"},
            {"id": "live_feeds", "value": governed_live_feed_count, "label": "live ticker feeds", "basis": "governed Live Intelligence source registry"},
        ],
        "featured_signal_count": featured_signal_count,
        "represented_source_count": represented_source_count,
        "latest_refresh": generated_at,
        "highlights": [_highlight(signal) for signal in signals[:4]],
        "entry_points": [
            {"id": "world", "label": "Explore the World", "href": "/app/?view=overview", "description": "Open the global map and current public evidence."},
            {"id": "earth", "label": "Earth & Environment", "href": "/app/?view=earth", "description": "Inspect Earth observation and environmental systems."},
            {"id": "ocean_space", "label": "Ocean & Space", "href": "/app/?view=science", "description": "Continue into marine and space observation workspaces."},
        ],
        "primary_action": {"label": "Open Site Intelligence", "href": "/app/?view=overview"},
        "truth_boundaries": [
            "Capability counts describe registered platform coverage and are intentionally separate from the bounded current-signal refresh.",
            "Enabled connectors may be live, cached, metadata-only, fallback-safe, or dependent on optional backend credentials.",
            "Live signals retain source, geography, freshness, methodology, and limitation context.",
            "The homepage summary degrades independently and does not boot the full Site Intelligence application.",
        ],
        "generated_at": generated_at,
    }
