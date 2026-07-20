"""Live Intelligence electronic ticker feed for Site Intelligence v3.1.0.

The feed exposes public-safe connector and platform signals. It reports source
readiness, freshness and platform state without exposing credentials, raw provider
payloads, private records, or unsupported automated interpretation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import Settings
from .connected_public_intelligence_v300 import ConnectedPublicIntelligencePlatform
from .public_live_connectors import CONNECTORS, ENVIRONMENTAL_SUBCONNECTORS, _reliability_for
from .alerts_monitoring_live_streams import monitoring_config
from .version import APP_VERSION, RELEASE_NAME

SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.0"
CATEGORY_ALIASES = {
    "all": "",
    "planet": "earth_systems",
    "earth": "earth_systems",
    "society": "human_systems",
    "economy": "economy_resources",
    "platform": "platform",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signal(*, signal_id: str, category: str, label: str, value: str, source: str,
            status: str, destination: str, updated_at: str, detail: str = "",
            source_url: str = "") -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "category": category,
        "label": label,
        "value": value,
        "unit": "",
        "status": status,
        "severity": "informational" if status not in {"degraded", "stale"} else "attention",
        "source_name": source,
        "source_url": source_url,
        "updated_at": updated_at,
        "observed_at": updated_at,
        "destination_url": destination,
        "detail": detail,
    }


def build_live_intelligence(settings: Settings, *, category: str = "", limit: int = 8) -> dict[str, Any]:
    generated_at = _now()
    requested = CATEGORY_ALIASES.get((category or "").strip().lower(), (category or "").strip().lower())
    limit = max(1, min(int(limit), 20))

    connected = ConnectedPublicIntelligencePlatform(settings).overview()
    monitor = monitoring_config(settings)
    connector_states = [_reliability_for(item, settings) for item in CONNECTORS]
    healthy = sum(1 for item in connector_states if item.get("level") == "healthy")

    signals: list[dict[str, Any]] = [
        _signal(
            signal_id="platform.site-intelligence-api",
            category="platform",
            label="SITE INTELLIGENCE API",
            value=f"v{APP_VERSION} ONLINE",
            source="Sustainable Catalyst",
            status="current",
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail=RELEASE_NAME,
        ),
        _signal(
            signal_id="platform.connected-public-index",
            category="platform",
            label="CONNECTED PUBLIC INDEX",
            value=f"{connected.get('record_count', 0)} RECORDS",
            source="Site Intelligence",
            status="current",
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Public-safe records available through the connected evidence layer.",
        ),
        _signal(
            signal_id="platform.connector-readiness",
            category="platform",
            label="PUBLIC API CONNECTORS",
            value=f"{healthy}/{len(CONNECTORS)} HEALTHY",
            source="Connector Registry",
            status="current" if healthy else "degraded",
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Live, cached and fallback-safe connector readiness.",
        ),
        _signal(
            signal_id="earth.environmental-sources",
            category="earth_systems",
            label="EARTH SYSTEM SOURCES",
            value=f"{len(ENVIRONMENTAL_SUBCONNECTORS)} SOURCES",
            source="NASA · NOAA · EPA · EIA · USGS · GBIF",
            status="current",
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Environmental sources are displayed through live, cached or fallback-safe modes.",
        ),
        _signal(
            signal_id="society.monitoring-stream",
            category="human_systems",
            label="MONITORING STREAM",
            value="ACTIVE" if monitor.enabled else "PAUSED",
            source="Site Intelligence",
            status="current" if monitor.enabled else "degraded",
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail="Public monitoring is informational and does not replace official emergency guidance.",
        ),
    ]

    category_map = {
        "world-bank": "economy_resources",
        "openalex": "research",
        "crossref": "research",
        "github": "platform",
        "environmental": "earth_systems",
    }
    for connector, reliability in zip(CONNECTORS, connector_states):
        label = f"{connector['label'].upper()} API"
        mode = reliability.get("display_mode", connector.get("status", "review")).replace("_", " ").upper()
        signals.append(_signal(
            signal_id=f"connector.{connector['slug']}",
            category=category_map.get(connector["slug"], "platform"),
            label=label,
            value=mode,
            source=connector["label"],
            status="current" if reliability.get("level") == "healthy" else reliability.get("level", "degraded"),
            destination="/platform/site-intelligence/",
            updated_at=generated_at,
            detail=connector.get("public_use", "Public connector status."),
        ))

    if requested:
        signals = [item for item in signals if item["category"] == requested]
    selected = signals[:limit]
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "generated_at": generated_at,
        "category": requested or "all",
        "count": len(selected),
        "signals": selected,
        "display": {
            "label": "Live Intelligence",
            "theme": "electronic",
            "default_motion": "slow",
            "source_attribution_required": True,
            "freshness_required": True,
        },
        "boundaries": [
            "Signals are public-safe summaries, not raw upstream API payloads.",
            "Connector readiness does not imply uninterrupted upstream availability.",
            "No investment, legal, emergency, or causal recommendation is generated.",
        ],
    }


def live_intelligence_status(settings: Settings) -> dict[str, Any]:
    payload = build_live_intelligence(settings, limit=20)
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "signal_count": payload["count"],
        "generated_at": payload["generated_at"],
        "service": "available",
        "cache_safe": bool(settings.external_cache_enabled),
    }
