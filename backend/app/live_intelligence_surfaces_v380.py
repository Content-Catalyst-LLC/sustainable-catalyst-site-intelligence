"""Connected, governed Live Intelligence surfaces for Site Intelligence v3.10.0.

This module turns the canonical Live Intelligence signal contract into reusable
public surfaces without duplicating ingestion, freshness, rotation, source, or
analytics logic. Surface policies may filter presentation and destinations, but
never alter observations, source lineage, or freshness states.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Mapping

from .version import APP_VERSION

SURFACE_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-surface/1.0"
SURFACE_POLICY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-surface-policy/1.0"
EMBED_MANIFEST_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-embed/1.0"

ALL_DESTINATIONS = (
    "signal_context", "site_intelligence_workspace", "evidence_record",
    "map_context", "decision_studio", "primary_source",
)

SURFACE_REGISTRY: dict[str, dict[str, Any]] = {
    "homepage": {
        "label": "Homepage Intelligence Gateway",
        "description": "The primary public Live Intelligence strip directly below the homepage hero.",
        "default_channel": "global", "default_limit": 8, "maximum_limit": 12,
        "presentation": "ticker", "reduced_motion": "static", "mobile_mode": "rotator",
        "allowed_families": [], "allowed_destinations": list(ALL_DESTINATIONS),
        "record_rotation_history": True, "embed_allowed": False,
        "shortcode": '[sc_live_intelligence surface="homepage" limit="8" max_visible="8"]',
        "placement": "directly_below_homepage_hero",
    },
    "static_strip": {
        "label": "Static Intelligence Strip",
        "description": "A compact, non-moving signal strip for institutional pages and narrow page sections.",
        "default_channel": "global", "default_limit": 6, "maximum_limit": 8,
        "presentation": "static", "reduced_motion": "static", "mobile_mode": "stacked",
        "allowed_families": [], "allowed_destinations": list(ALL_DESTINATIONS),
        "record_rotation_history": False, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_static limit="6"]',
        "placement": "inline_page_section",
    },
    "channel": {
        "label": "Channel Intelligence Surface",
        "description": "A channel-specific surface using the same governed signal and source contracts.",
        "default_channel": "global", "default_limit": 10, "maximum_limit": 12,
        "presentation": "manual", "reduced_motion": "manual", "mobile_mode": "rotator",
        "allowed_families": [], "allowed_destinations": list(ALL_DESTINATIONS),
        "record_rotation_history": True, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_channel channel="climate-earth" limit="10"]',
        "placement": "channel_landing_page",
    },
    "publication": {
        "label": "Publication Signal Insert",
        "description": "A restrained evidence-aware insert for publications and briefing pages.",
        "default_channel": "research", "default_limit": 3, "maximum_limit": 5,
        "presentation": "static", "reduced_motion": "static", "mobile_mode": "stacked",
        "allowed_families": ["publications_evidence", "science_environment", "institutional_indicators"],
        "allowed_destinations": ["signal_context", "evidence_record", "primary_source", "site_intelligence_workspace"],
        "record_rotation_history": False, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_publication limit="3"]',
        "placement": "publication_context_panel",
    },
    "library": {
        "label": "Knowledge Library Signal Panel",
        "description": "Research and evidence signals connected to Knowledge Library collections and pathways.",
        "default_channel": "research", "default_limit": 6, "maximum_limit": 8,
        "presentation": "manual", "reduced_motion": "manual", "mobile_mode": "stacked",
        "allowed_families": ["science_environment", "publications_evidence", "institutional_indicators"],
        "allowed_destinations": ["signal_context", "evidence_record", "site_intelligence_workspace", "primary_source"],
        "record_rotation_history": True, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_library limit="6"]',
        "placement": "library_collection_or_pathway",
    },
    "advisory": {
        "label": "Advisory Context Panel",
        "description": "A calm context panel for advisory pages without claims of personalized advice.",
        "default_channel": "global", "default_limit": 4, "maximum_limit": 6,
        "presentation": "static", "reduced_motion": "static", "mobile_mode": "stacked",
        "allowed_families": ["economics_development", "institutional_indicators", "climate_earth_systems", "energy_carbon"],
        "allowed_destinations": ["signal_context", "site_intelligence_workspace", "evidence_record", "primary_source"],
        "record_rotation_history": False, "embed_allowed": False,
        "shortcode": '[sc_live_intelligence_advisory limit="4"]',
        "placement": "advisory_context_panel",
    },
    "lab": {
        "label": "Lab Observation Strip",
        "description": "Scientific and environmental observations for the Sustainable Catalyst Lab.",
        "default_channel": "science-research", "default_limit": 8, "maximum_limit": 12,
        "presentation": "manual", "reduced_motion": "manual", "mobile_mode": "stacked",
        "allowed_families": ["climate_earth_systems", "energy_carbon", "science_environment"],
        "allowed_destinations": ["signal_context", "map_context", "evidence_record", "site_intelligence_workspace", "primary_source"],
        "record_rotation_history": True, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_lab limit="8"]',
        "placement": "lab_observation_workspace",
    },
    "external_embed": {
        "label": "Public-Safe External Embed",
        "description": "A bounded public embed that cannot expose administrative controls or private operational metadata.",
        "default_channel": "global", "default_limit": 6, "maximum_limit": 8,
        "presentation": "static", "reduced_motion": "static", "mobile_mode": "stacked",
        "allowed_families": [],
        "allowed_destinations": ["signal_context", "site_intelligence_workspace", "evidence_record", "map_context", "primary_source"],
        "record_rotation_history": False, "embed_allowed": True,
        "shortcode": '[sc_live_intelligence_embed limit="6"]',
        "placement": "approved_external_embed",
    },
}

SURFACE_ALIASES = {
    "feed": "static_strip", "static": "static_strip", "strip": "static_strip",
    "knowledge_library": "library", "research_library": "library",
    "publication_insert": "publication", "lab_observations": "lab", "embed": "external_embed",
}


def normalize_surface_id(value: Any) -> str:
    cleaned = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    cleaned = SURFACE_ALIASES.get(cleaned, cleaned)
    if cleaned not in SURFACE_REGISTRY:
        raise KeyError(cleaned or "unknown")
    return cleaned


def surface_definition(surface_id: str) -> dict[str, Any]:
    normalized = normalize_surface_id(surface_id)
    item = deepcopy(SURFACE_REGISTRY[normalized])
    item.update({
        "surface_id": normalized,
        "schema": SURFACE_SCHEMA_VERSION,
        "version": APP_VERSION,
        "feed_url": f"/public/live-intelligence/surfaces/{normalized}/feed",
        "definition_url": f"/public/live-intelligence/surfaces/{normalized}",
        "policy_url": "/public/live-intelligence/surface-policy",
    })
    return item


def surface_directory() -> dict[str, Any]:
    surfaces = [surface_definition(surface_id) for surface_id in SURFACE_REGISTRY]
    return {
        "ok": True, "version": APP_VERSION, "schema": SURFACE_SCHEMA_VERSION,
        "count": len(surfaces), "surfaces": surfaces,
        "canonical_feed": "/public/live-intelligence",
        "surface_policy_url": "/public/live-intelligence/surface-policy",
        "governance": {
            "single_canonical_signal_contract": True,
            "separate_ingestion_per_surface": False,
            "freshness_rules_bypassable": False,
            "private_metadata_exposed": False,
            "advertising_or_affiliate_signals": False,
        },
    }


def surface_policy() -> dict[str, Any]:
    return {
        "ok": True, "version": APP_VERSION, "schema": SURFACE_POLICY_SCHEMA_VERSION,
        "principle": "One governed signal system, many bounded public presentations.",
        "surface_count": len(SURFACE_REGISTRY),
        "canonical_contracts": {
            "source_operations": "/public/live-intelligence/sources",
            "freshness_status": "/public/live-intelligence/status",
            "gateway": "/public/live-intelligence/gateway-policy",
            "rotation": "/public/live-intelligence/rotation-policy",
            "analytics": "/public/live-intelligence/analytics-policy",
            "presentation": "/public/live-intelligence/presentation-policy",
        },
        "boundaries": [
            "Surfaces may filter or cap signals but may not rewrite source observations.",
            "Every surface retains source, time, freshness, lineage, and responsible-use metadata.",
            "External embeds cannot expose administrative endpoints, private state, or API credentials.",
            "No surface may bypass validation, expiry suppression, or same-query last-known-good rules.",
            "Advertising, sponsored items, and affiliate promotions are not Live Intelligence signals.",
        ],
        "surfaces": [surface_definition(surface_id) for surface_id in SURFACE_REGISTRY],
    }


def _allowed_destination(signal: Mapping[str, Any], allowlist: set[str]) -> dict[str, Any] | None:
    candidates = []
    primary = signal.get("primary_destination")
    if isinstance(primary, Mapping):
        candidates.append(dict(primary))
    for item in signal.get("secondary_destinations") or []:
        if isinstance(item, Mapping):
            candidates.append(dict(item))
    for item in candidates:
        if str(item.get("type") or "") in allowlist and str(item.get("url") or "").startswith(("/", "https://", "http://")):
            return item
    return None


def apply_connected_surface_policy(payload: Mapping[str, Any], surface_id: str, *, limit: int | None = None) -> dict[str, Any]:
    normalized = normalize_surface_id(surface_id)
    definition = surface_definition(normalized)
    output = deepcopy(dict(payload))
    signals = [deepcopy(dict(item)) for item in output.get("signals") or [] if isinstance(item, Mapping)]
    allowed_families = set(definition["allowed_families"])
    if allowed_families:
        signals = [item for item in signals if str(item.get("signal_family") or "") in allowed_families]
    cap = definition["default_limit"] if limit is None else int(limit)
    cap = max(1, min(cap, int(definition["maximum_limit"])))
    allowlist = set(definition["allowed_destinations"])
    prepared: list[dict[str, Any]] = []
    for item in signals[:cap]:
        allowed_primary = _allowed_destination(item, allowlist)
        if allowed_primary:
            item["primary_destination"] = allowed_primary
            item["destination_type"] = allowed_primary.get("type") or "signal_context"
        item["secondary_destinations"] = [
            destination for destination in (item.get("secondary_destinations") or [])
            if isinstance(destination, Mapping) and str(destination.get("type") or "") in allowlist
        ]
        item.update({
            "surface_id": normalized,
            "surface_label": definition["label"],
            "surface_position": len(prepared) + 1,
            "surface_presentation": definition["presentation"],
            "embed_safe": bool(definition["embed_allowed"]),
        })
        prepared.append(item)
    output["signals"] = prepared
    output["count"] = len(prepared)
    output["surface_schema"] = SURFACE_SCHEMA_VERSION
    output["surface"] = {
        key: value for key, value in definition.items()
        if key not in {"allowed_destinations", "allowed_families"}
    }
    output["surface"]["allowed_destination_types"] = list(definition["allowed_destinations"])
    output["surface"]["allowed_signal_families"] = list(definition["allowed_families"])
    output["surface"]["requested_limit"] = cap
    output["surface"]["family_counts"] = dict(Counter(str(item.get("signal_family") or "unknown") for item in prepared))
    output["surface"]["source_count"] = len({str(item.get("feed_id") or item.get("source_id") or "") for item in prepared if item.get("feed_id") or item.get("source_id")})
    output.setdefault("display", {})
    output["display"].update({
        "surface_id": normalized,
        "presentation": definition["presentation"],
        "reduced_motion": definition["reduced_motion"],
        "mobile_mode": definition["mobile_mode"],
        "placement": definition["placement"],
    })
    output.setdefault("boundaries", [])
    for boundary in surface_policy()["boundaries"]:
        if boundary not in output["boundaries"]:
            output["boundaries"].append(boundary)
    return output


def embed_manifest(surface_id: str = "external_embed") -> dict[str, Any]:
    definition = surface_definition(surface_id)
    if not definition["embed_allowed"]:
        raise ValueError("This Live Intelligence surface is not approved for embedding.")
    return {
        "ok": True, "version": APP_VERSION, "schema": EMBED_MANIFEST_SCHEMA_VERSION,
        "surface": definition,
        "feed_url": definition["feed_url"],
        "cache": {"public": True, "recommended_max_age_seconds": 120, "stale_while_revalidate_seconds": 600},
        "security": {
            "api_credentials_in_browser": False,
            "administrative_routes_exposed": False,
            "arbitrary_signal_injection": False,
            "allowed_destination_types": definition["allowed_destinations"],
            "recommended_referrer_policy": "strict-origin-when-cross-origin",
        },
        "accessibility": {
            "reduced_motion_supported": True,
            "keyboard_navigation_supported": True,
            "static_fallback_supported": True,
        },
    }
