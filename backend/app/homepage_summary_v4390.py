"""Public-safe homepage summary for Site Intelligence v4.39.0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .version import APP_VERSION


SCHEMA_VERSION = "sc-site-intelligence-home-summary/1.0"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
COUNTRY_REGISTRY = DATA_DIR / "country_identity_registry_v43523.json"
SOURCE_REGISTRY = DATA_DIR / "live_intelligence_source_registry_v320.json"


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


def _source_counts() -> tuple[int, int]:
    registry = _read_json(SOURCE_REGISTRY)
    sources = registry.get("sources") if isinstance(registry.get("sources"), list) else []
    enabled = sum(1 for source in sources if isinstance(source, Mapping) and source.get("default_enabled") is True)
    return len(sources), enabled


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


def build_homepage_summary(live_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a small, auditable payload without booting the full public app."""
    payload = dict(live_payload or {})
    signals = [signal for signal in (payload.get("signals") or []) if isinstance(signal, Mapping)]
    source_count, enabled_source_count = _source_counts()
    country_count = _country_count()
    gateway = payload.get("gateway") if isinstance(payload.get("gateway"), Mapping) else {}
    represented_source_count = max(0, int(gateway.get("represented_source_count") or 0))
    generated_at = _bounded_text(payload.get("generated_at"), 80)
    live_count = len(signals)

    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "title": "Site Intelligence",
        "summary": "Explore geographic, environmental, humanitarian, scientific, and institutional evidence through a provenance-aware public intelligence system.",
        "status": {
            "state": "online",
            "label": "Site Intelligence Online",
            "delivery_state": "live" if live_count else "available",
            "message": "Current public signals are available." if live_count else "The platform is available; no current signals were returned for this refresh.",
        },
        "metrics": [
            {"id": "country_profiles", "value": country_count, "label": "country profiles", "basis": "first-party country identity registry"},
            {"id": "registered_sources", "value": source_count, "label": "registered live feeds", "basis": "Live Intelligence source registry"},
            {"id": "enabled_sources", "value": enabled_source_count, "label": "enabled by default", "basis": "Live Intelligence source policy"},
            {"id": "current_signals", "value": live_count, "label": "current signals", "basis": "bounded homepage refresh"},
        ],
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
            "Counts describe registered platform coverage and the current bounded response; they do not imply uniform observations for every country or source.",
            "Live signals retain source, geography, freshness, methodology, and limitation context.",
            "The homepage summary degrades independently and does not boot the full Site Intelligence application.",
        ],
        "generated_at": generated_at,
    }
