"""Homepage gateway contracts for Live Intelligence v3.13.0.

This module enriches the existing reliable signal feed with public-facing signal
families, geography, and a deterministic destination hierarchy. It does not
change source observations, ranking scores, or freshness classification.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping
from urllib.parse import quote

from .version import APP_VERSION

GATEWAY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-gateway/1.0"
DEFAULT_HOMEPAGE_SIGNAL_LIMIT = 8
MAX_HOMEPAGE_SIGNAL_LIMIT = 12

SIGNAL_FAMILY_REGISTRY: dict[str, dict[str, str]] = {
    "climate_earth_systems": {
        "label": "Climate & Earth Systems",
        "description": "Weather, geophysical hazards, climate, and Earth-observation signals.",
        "workspace_url": "/platform/site-intelligence/?view=earth",
    },
    "energy_carbon": {
        "label": "Energy & Carbon",
        "description": "Energy, emissions, carbon-intensity, and resource-system signals.",
        "workspace_url": "/platform/site-intelligence/?view=resources",
    },
    "economics_development": {
        "label": "Economics & Development",
        "description": "Economic, development, trade, and institutional indicator signals.",
        "workspace_url": "/platform/site-intelligence/?view=economics",
    },
    "humanitarian_conditions": {
        "label": "Humanitarian Conditions",
        "description": "Humanitarian, displacement, conflict, and human-security signals.",
        "workspace_url": "/platform/site-intelligence/?view=humanitarian",
    },
    "science_environment": {
        "label": "Science & Environment",
        "description": "Open research, scientific publication, and environmental observation signals.",
        "workspace_url": "/platform/site-intelligence/?view=research",
    },
    "institutional_indicators": {
        "label": "Institutional Indicators",
        "description": "Governance, law, public-institution, and international-system signals.",
        "workspace_url": "/platform/site-intelligence/?view=governance",
    },
    "platform_operations": {
        "label": "Platform Operations",
        "description": "Sustainable Catalyst platform availability and connected-feed status.",
        "workspace_url": "/platform/site-intelligence/",
    },
    "publications_evidence": {
        "label": "Publications & Evidence",
        "description": "New evidence records, briefings, publications, and research-path signals.",
        "workspace_url": "/publications/",
    },
}

FEED_FAMILY_MAP = {
    "noaa_nws": "climate_earth_systems",
    "usgs_earthquakes": "climate_earth_systems",
    "nasa_eonet": "climate_earth_systems",
    "nasa_power": "energy_carbon",
    "reliefweb": "humanitarian_conditions",
    "openalex": "science_environment",
    "world_bank": "economics_development",
    "platform_status": "platform_operations",
}

CATEGORY_FAMILY_MAP = {
    "earth_systems": "climate_earth_systems",
    "human_systems": "humanitarian_conditions",
    "research": "science_environment",
    "economy_resources": "economics_development",
    "platform": "platform_operations",
}

DESTINATION_HIERARCHY = [
    {"rank": 1, "type": "signal_context", "label": "Signal context", "purpose": "Explain the signal, freshness, source lineage, and limitations."},
    {"rank": 2, "type": "site_intelligence_workspace", "label": "Site Intelligence workspace", "purpose": "Continue into the most relevant analytical workspace."},
    {"rank": 3, "type": "evidence_record", "label": "Evidence record", "purpose": "Inspect a structured evidence payload for the selected signal."},
    {"rank": 4, "type": "map_context", "label": "Map context", "purpose": "Open geographic context when source coordinates are available."},
    {"rank": 5, "type": "decision_studio", "label": "Decision Studio", "purpose": "Carry the signal into a human-controlled decision workflow."},
    {"rank": 6, "type": "primary_source", "label": "Primary source", "purpose": "Open the represented public source."},
]


def _clean(value: Any, limit: int = 180) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_url(value: Any) -> str:
    candidate = str(value or "").strip()
    return candidate[:1200] if candidate.startswith(("https://", "http://", "/")) else ""


def _family_id(signal: Mapping[str, Any]) -> str:
    explicit = _clean(signal.get("signal_family"), 80)
    if explicit in SIGNAL_FAMILY_REGISTRY:
        return explicit
    feed_id = _clean(signal.get("feed_id"), 80)
    if feed_id in FEED_FAMILY_MAP:
        return FEED_FAMILY_MAP[feed_id]
    category = _clean(signal.get("category"), 80)
    return CATEGORY_FAMILY_MAP.get(category, "institutional_indicators")


def _geography(signal: Mapping[str, Any]) -> dict[str, Any]:
    country = _clean(signal.get("country"), 100)
    country_code = _clean(signal.get("country_code"), 12).upper()
    region = _clean(signal.get("region"), 100)
    location = _clean(signal.get("location_label"), 160)
    coords = signal.get("coordinates")
    longitude = latitude = None
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            longitude = float(coords[0])
            latitude = float(coords[1])
        except (TypeError, ValueError):
            longitude = latitude = None
    label = location or country or region or "Global"
    scope = "local" if location else "country" if country else "regional" if region else "global"
    map_url = ""
    if longitude is not None and latitude is not None:
        map_url = f"https://www.openstreetmap.org/?mlat={latitude:.6f}&mlon={longitude:.6f}#map=6/{latitude:.6f}/{longitude:.6f}"
    return {
        "scope": scope,
        "label": label,
        "country": country,
        "country_code": country_code,
        "region": region,
        "longitude": longitude,
        "latitude": latitude,
        "map_url": map_url,
    }


def _destination(destination_type: str, label: str, url: str, *, rank: int, description: str = "") -> dict[str, Any] | None:
    safe_url = _safe_url(url)
    if not safe_url:
        return None
    return {
        "type": destination_type,
        "label": label,
        "url": safe_url,
        "rank": rank,
        "description": _clean(description, 220),
    }


def _dedupe_destinations(destinations: Iterable[dict[str, Any] | None]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for destination in destinations:
        if not destination:
            continue
        key = (str(destination.get("type") or ""), str(destination.get("url") or ""))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        output.append(destination)
    return sorted(output, key=lambda item: int(item.get("rank") or 99))


def enrich_gateway_signal(signal: Mapping[str, Any]) -> dict[str, Any]:
    item = deepcopy(dict(signal))
    signal_id = _clean(item.get("signal_id"), 180)
    family_id = _family_id(item)
    family = SIGNAL_FAMILY_REGISTRY[family_id]
    geography = _geography(item)
    encoded = quote(signal_id, safe="")

    context_url = _safe_url(item.get("context_view_url") or item.get("context_url"))
    workspace_url = _safe_url(item.get("destination_url")) or family["workspace_url"]
    evidence_url = _safe_url(item.get("evidence_url"))
    source_url = _safe_url(item.get("source_url"))
    decision_url = f"/platform/decision-studio/?source=live-intelligence&signal={encoded}" if signal_id else ""

    destinations = _dedupe_destinations([
        _destination("signal_context", "Open signal context", context_url, rank=1, description="Review freshness, evidence lineage, methodology, and limitations."),
        _destination("site_intelligence_workspace", f"Open {family['label']} workspace", workspace_url, rank=2, description="Continue into the relevant Site Intelligence workspace."),
        _destination("evidence_record", "Open evidence record", evidence_url, rank=3, description="Inspect a structured evidence payload for this signal."),
        _destination("map_context", "Open map context", geography["map_url"], rank=4, description="Inspect source-provided geographic context."),
        _destination("decision_studio", "Send to Decision Studio", decision_url, rank=5, description="Carry the signal into a human-controlled decision workflow."),
        _destination("primary_source", "Open primary source", source_url, rank=6, description="Open the represented public source."),
    ])
    primary = destinations[0] if destinations else {
        "type": "site_intelligence_workspace",
        "label": "Open Site Intelligence",
        "url": "/platform/site-intelligence/",
        "rank": 2,
        "description": "Open the connected public-intelligence platform.",
    }

    item.update({
        "short_label": _clean(item.get("short_label") or item.get("label"), 72),
        "formatted_value": _clean(item.get("formatted_value") or item.get("value"), 220),
        "signal_family": family_id,
        "family_label": family["label"],
        "family_description": family["description"],
        "geography": geography,
        "geography_label": geography["label"],
        "primary_destination": primary,
        "secondary_destinations": [entry for entry in destinations if entry != primary],
        "destination_type": primary["type"],
        "homepage_eligible": item.get("validation_state") != "invalid",
        "priority_score": int(item.get("selection_score") or item.get("priority") or 0),
        "methodology_note": _clean(item.get("methodology_note") or "Review the signal context for source, freshness, and selection-method details.", 260),
        "responsible_use_note": _clean(item.get("responsible_use_note") or "This signal is informational and should be interpreted with its source, time, geography, and limitations.", 260),
    })
    return item


def apply_gateway_policy(payload: Mapping[str, Any], *, surface: str = "feed") -> dict[str, Any]:
    result = deepcopy(dict(payload))
    signals = [enrich_gateway_signal(item) for item in (result.get("signals") or []) if isinstance(item, Mapping)]
    result["signals"] = signals
    result["count"] = len(signals)
    family_counts = Counter(str(item.get("signal_family") or "institutional_indicators") for item in signals)
    geography_counts = Counter(str((item.get("geography") or {}).get("scope") or "global") for item in signals)
    destination_counts = Counter(str((item.get("primary_destination") or {}).get("type") or "unknown") for item in signals)
    represented_sources = sorted({_clean(item.get("source_name"), 160) for item in signals if _clean(item.get("source_name"), 160)})

    result["gateway_schema"] = GATEWAY_SCHEMA_VERSION
    result["gateway"] = {
        "surface": "homepage" if surface == "homepage" else "feed",
        "label": "Live Intelligence",
        "default_homepage_signal_limit": DEFAULT_HOMEPAGE_SIGNAL_LIMIT,
        "maximum_homepage_signal_limit": MAX_HOMEPAGE_SIGNAL_LIMIT,
        "signal_family_count": len(family_counts),
        "family_counts": dict(family_counts),
        "geography_counts": dict(geography_counts),
        "primary_destination_counts": dict(destination_counts),
        "represented_source_count": len(represented_sources),
        "represented_sources": represented_sources,
        "family_registry_url": "/public/live-intelligence/gateway-policy",
        "homepage_feed_url": "/public/live-intelligence/homepage",
        "destination_hierarchy": [entry["type"] for entry in DESTINATION_HIERARCHY],
    }
    display = dict(result.get("display") or {})
    display.update({
        "homepage_gateway_supported": True,
        "signal_families_supported": True,
        "structured_geography_supported": True,
        "primary_secondary_destinations_supported": True,
        "default_homepage_signal_limit": DEFAULT_HOMEPAGE_SIGNAL_LIMIT,
        "recommended_homepage_position": "directly_below_hero",
        "homepage_sticky_behavior": "disabled",
        "full_application_boot_required": False,
    })
    result["display"] = display
    boundaries = list(result.get("boundaries") or [])
    for boundary in (
        "Homepage destinations follow a transparent hierarchy: context, workspace, evidence, map, Decision Studio, then primary source.",
        "Signal families organize public navigation; they do not change the source observation or imply causal relationships.",
        "The homepage feed is intentionally bounded and does not load the full Site Intelligence application.",
    ):
        if boundary not in boundaries:
            boundaries.append(boundary)
    result["boundaries"] = boundaries
    return result


def homepage_gateway_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": GATEWAY_SCHEMA_VERSION,
        "name": "Live Intelligence Homepage Gateway",
        "default_signal_limit": DEFAULT_HOMEPAGE_SIGNAL_LIMIT,
        "maximum_signal_limit": MAX_HOMEPAGE_SIGNAL_LIMIT,
        "recommended_placement": "Directly below the homepage hero",
        "sticky": False,
        "signal_families": [
            {"id": family_id, **metadata}
            for family_id, metadata in SIGNAL_FAMILY_REGISTRY.items()
        ],
        "destination_hierarchy": DESTINATION_HIERARCHY,
        "required_signal_fields": [
            "signal_id", "short_label", "formatted_value", "unit", "status",
            "signal_family", "geography", "observed_at", "updated_at",
            "freshness_state", "source_name", "source_url",
            "primary_destination", "secondary_destinations", "methodology_note",
            "responsible_use_note", "priority_score", "homepage_eligible",
        ],
        "principles": [
            "Every homepage signal opens a useful next step.",
            "Context and evidence are preferred before an external source handoff.",
            "The signal time, geography, source, and freshness remain visible and machine-readable.",
            "The gateway does not fabricate values, infer causation, or publish automated emergency claims.",
        ],
    }
