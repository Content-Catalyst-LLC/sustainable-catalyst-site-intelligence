"""Topic and regional Live Intelligence channels for Site Intelligence v3.11.0.

Channels are transparent filters over the existing public-signal service. They
never fabricate missing local context, infer country identity from coordinates,
or silently replace an empty regional result with unrelated global signals.
"""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Iterable, Mapping

from .config import Settings
from .version import APP_VERSION
from . import live_intelligence_v314 as base

CHANNEL_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-channels/1.0"
CHANNEL_POLICY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-channel-policy/1.0"

# Country-code groups are explicit routing aids, not geopolitical judgments.
REGION_COUNTRY_CODES = {
    "africa": {
        "DZ","AO","BJ","BW","BF","BI","CV","CM","CF","TD","KM","CG","CD","CI","DJ","EG","GQ","ER","SZ","ET","GA","GM","GH","GN","GW","KE","LS","LR","LY","MG","MW","ML","MR","MU","MA","MZ","NA","NE","NG","RW","ST","SN","SC","SL","SO","ZA","SS","SD","TZ","TG","TN","UG","ZM","ZW",
    },
    "americas": {
        "AG","AR","BS","BB","BZ","BO","BR","CA","CL","CO","CR","CU","DM","DO","EC","SV","GD","GT","GY","HT","HN","JM","MX","NI","PA","PY","PE","KN","LC","VC","SR","TT","US","UY","VE",
    },
    "asia-pacific": {
        "AF","AU","BD","BT","BN","KH","CN","FJ","IN","ID","JP","KI","KP","KR","LA","MY","MV","MH","FM","MN","MM","NR","NP","NZ","PK","PW","PG","PH","WS","SG","SB","LK","TH","TL","TO","TV","VU","VN",
    },
    "europe": {
        "AL","AD","AT","BY","BE","BA","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IS","IE","IT","XK","LV","LI","LT","LU","MT","MD","MC","ME","NL","MK","NO","PL","PT","RO","RU","SM","RS","SK","SI","ES","SE","CH","UA","GB","VA",
    },
    "middle-east-north-africa": {
        "DZ","BH","EG","IR","IQ","IL","JO","KW","LB","LY","MA","OM","PS","QA","SA","SY","TN","TR","AE","YE",
    },
}

REGION_ALIASES = {
    "global": "global",
    "world": "global",
    "worldwide": "global",
    "africa": "africa",
    "sub-saharan-africa": "africa",
    "americas": "americas",
    "north-america": "americas",
    "latin-america": "americas",
    "south-america": "americas",
    "asia": "asia-pacific",
    "asia-pacific": "asia-pacific",
    "apac": "asia-pacific",
    "oceania": "asia-pacific",
    "europe": "europe",
    "mena": "middle-east-north-africa",
    "middle-east": "middle-east-north-africa",
    "middle-east-north-africa": "middle-east-north-africa",
}

CHANNEL_REGISTRY: dict[str, dict[str, Any]] = {
    "global": {
        "label": "Global Intelligence",
        "description": "Balanced public-interest signals across all enabled sources and categories.",
        "kind": "global",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "global",
    },
    "earth-systems": {
        "label": "Earth Systems",
        "description": "Earthquakes, natural events, weather, climate, and environmental observations.",
        "kind": "topic",
        "categories": ["earth_systems"],
        "feeds": ["noaa_nws", "usgs_earthquakes", "nasa_eonet", "nasa_power"],
        "keywords": [],
    },
    "weather-climate": {
        "label": "Weather and Climate",
        "description": "Weather alerts, temperature, precipitation, storms, drought, heat, and climate observations.",
        "kind": "topic",
        "categories": ["earth_systems"],
        "feeds": ["noaa_nws", "nasa_eonet", "nasa_power"],
        "keywords": ["weather", "climate", "storm", "temperature", "precipitation", "drought", "heat", "flood", "wildfire", "cyclone", "hurricane", "typhoon"],
    },
    "humanitarian": {
        "label": "Humanitarian Conditions",
        "description": "Humanitarian reports, displacement, conflict-related public records, and affected-location coverage.",
        "kind": "topic",
        "categories": ["human_systems"],
        "feeds": ["reliefweb"],
        "keywords": [],
    },
    "economy-energy-resources": {
        "label": "Economy, Energy and Resources",
        "description": "Development, economic, energy, resource, and sustainability indicators with explicit data years.",
        "kind": "topic",
        "categories": ["economy_resources"],
        "feeds": ["world_bank"],
        "keywords": [],
    },
    "science-research": {
        "label": "Science and Research",
        "description": "Recent open research metadata and related public scientific records.",
        "kind": "topic",
        "categories": ["research"],
        "feeds": ["openalex"],
        "keywords": [],
    },
    "infrastructure-resilience": {
        "label": "Infrastructure and Resilience",
        "description": "Signals explicitly mentioning infrastructure, resilience, energy systems, transport, water, or public-service continuity.",
        "kind": "topic",
        "categories": ["earth_systems", "human_systems", "economy_resources", "research"],
        "feeds": [],
        "keywords": ["infrastructure", "resilience", "grid", "energy", "transport", "water", "power", "housing", "bridge", "road", "communications", "recovery"],
        "require_keyword": True,
    },
    "africa": {
        "label": "Africa",
        "description": "Signals whose source records explicitly identify an African country or region.",
        "kind": "region",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "africa",
    },
    "americas": {
        "label": "The Americas",
        "description": "Signals whose source records explicitly identify a country or region in the Americas.",
        "kind": "region",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "americas",
    },
    "asia-pacific": {
        "label": "Asia-Pacific",
        "description": "Signals whose source records explicitly identify an Asia-Pacific country or region.",
        "kind": "region",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "asia-pacific",
    },
    "europe": {
        "label": "Europe",
        "description": "Signals whose source records explicitly identify a European country or region.",
        "kind": "region",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "europe",
    },
    "middle-east-north-africa": {
        "label": "Middle East and North Africa",
        "description": "Signals whose source records explicitly identify a country or region in the Middle East or North Africa.",
        "kind": "region",
        "categories": [],
        "feeds": [],
        "keywords": [],
        "region": "middle-east-north-africa",
    },
}

CHANNEL_ALIASES = {
    "all": "global",
    "world": "global",
    "earth": "earth-systems",
    "planet": "earth-systems",
    "weather": "weather-climate",
    "climate": "weather-climate",
    "human-systems": "humanitarian",
    "economy": "economy-energy-resources",
    "resources": "economy-energy-resources",
    "research": "science-research",
    "science": "science-research",
    "infrastructure": "infrastructure-resilience",
    "resilience": "infrastructure-resilience",
    "mena": "middle-east-north-africa",
    "apac": "asia-pacific",
}


def _slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return CHANNEL_ALIASES.get(text, text)


def _normalized_text(*values: Any) -> str:
    return " ".join(" ".join(str(value or "").split()).lower() for value in values if value)


def _channel_record(channel_id: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": channel_id,
        "label": str(metadata.get("label") or channel_id),
        "description": str(metadata.get("description") or ""),
        "kind": str(metadata.get("kind") or "topic"),
        "categories": list(metadata.get("categories") or []),
        "feeds": list(metadata.get("feeds") or []),
        "region": str(metadata.get("region") or ""),
        "country_parameter_supported": True,
        "region_parameter_supported": True,
        "shortcode": f'[sc_live_intelligence channel="{channel_id}"]',
        "feed_url": f"/public/live-intelligence/channels/{channel_id}/feed",
    }


def channel_directory() -> dict[str, Any]:
    channels = [_channel_record(channel_id, metadata) for channel_id, metadata in CHANNEL_REGISTRY.items()]
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": CHANNEL_SCHEMA_VERSION,
        "count": len(channels),
        "channels": channels,
        "default_channel": "global",
        "policy_url": "/public/live-intelligence/channel-policy",
        "boundaries": [
            "Channels filter already-selected public signals and do not create new facts.",
            "Geographic matching uses explicit source country, country-code, region, or location text only.",
            "An empty regional channel remains empty; it is not silently replaced with unrelated global signals.",
        ],
    }


def channel_definition(channel_id: str) -> dict[str, Any]:
    resolved = _slug(channel_id or "global") or "global"
    if resolved not in CHANNEL_REGISTRY:
        raise KeyError(resolved)
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": CHANNEL_SCHEMA_VERSION,
        "channel": _channel_record(resolved, CHANNEL_REGISTRY[resolved]),
        "policy_url": "/public/live-intelligence/channel-policy",
    }


def channel_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": CHANNEL_POLICY_SCHEMA_VERSION,
        "selection_order": [
            "Apply the named channel's category and source constraints.",
            "Apply explicit country or region constraints from source-supplied fields.",
            "Apply required topic keywords only for channels that declare them.",
            "Preserve the existing clustering, ranking, source caps, and freshness rules.",
        ],
        "capabilities": [
            "global, topic, regional, and country-filtered channels",
            "shortcode and REST channel selection",
            "transparent channel metadata and match reasons",
            "empty-result honesty without silent global fallback",
        ],
        "non_claims": [
            "Channels are not exhaustive situation reports.",
            "Regional membership does not imply a political or legal position.",
            "Country matching does not infer location from coordinates when source labels are absent.",
            "Channel inclusion does not certify truth, severity, or causal relevance.",
        ],
    }


def _region_id(value: str) -> str:
    slug = _slug(value)
    return REGION_ALIASES.get(slug, slug)


def _signal_geography(signal: Mapping[str, Any]) -> tuple[str, str]:
    code = str(signal.get("country_code") or "").strip().upper()
    text = _normalized_text(
        signal.get("country"), signal.get("region"), signal.get("location_label"),
        signal.get("value"), signal.get("detail"),
    )
    return code, text


def _matches_country(signal: Mapping[str, Any], country: str) -> bool:
    query = str(country or "").strip()
    if not query:
        return True
    code, text = _signal_geography(signal)
    upper = query.upper()
    if len(upper) in {2, 3} and code == upper:
        return True
    clean = _normalized_text(query)
    return bool(clean and clean in text)


def _matches_region(signal: Mapping[str, Any], region: str) -> bool:
    resolved = _region_id(region)
    if not resolved or resolved == "global":
        return True
    code, text = _signal_geography(signal)
    if code and code in REGION_COUNTRY_CODES.get(resolved, set()):
        return True
    region_terms = {
        "africa": ["africa", "african"],
        "americas": ["americas", "north america", "latin america", "south america", "caribbean"],
        "asia-pacific": ["asia", "asian", "pacific", "oceania"],
        "europe": ["europe", "european"],
        "middle-east-north-africa": ["middle east", "north africa", "mena"],
    }.get(resolved, [resolved.replace("-", " ")])
    return any(term in text for term in region_terms)


def _matches_topic(signal: Mapping[str, Any], definition: Mapping[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    categories = set(definition.get("categories") or [])
    feeds = set(definition.get("feeds") or [])
    if categories and str(signal.get("category") or "") not in categories:
        return False, []
    if categories:
        reasons.append("channel category")
    if feeds and str(signal.get("feed_id") or "") not in feeds:
        return False, []
    if feeds:
        reasons.append("channel source")
    keywords = [str(value).lower() for value in (definition.get("keywords") or []) if value]
    if keywords:
        text = _normalized_text(signal.get("label"), signal.get("value"), signal.get("detail"), signal.get("event_category"))
        hits = [word for word in keywords if word in text]
        if definition.get("require_keyword") and not hits:
            return False, []
        if hits:
            reasons.append("topic terms: " + ", ".join(hits[:3]))
    return True, reasons


def filter_channel_signals(
    signals: Iterable[Mapping[str, Any]],
    *,
    channel_id: str = "global",
    region: str = "",
    country: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved = _slug(channel_id or "global") or "global"
    if resolved not in CHANNEL_REGISTRY:
        raise KeyError(resolved)
    definition = CHANNEL_REGISTRY[resolved]
    effective_region = _region_id(region or str(definition.get("region") or ""))
    output: list[dict[str, Any]] = []
    for original in signals:
        signal = dict(original)
        topic_ok, reasons = _matches_topic(signal, definition)
        if not topic_ok:
            continue
        if country and not _matches_country(signal, country):
            continue
        if effective_region and effective_region != "global" and not _matches_region(signal, effective_region):
            continue
        if country:
            reasons.append("explicit country match")
        elif effective_region and effective_region != "global":
            reasons.append("explicit regional match")
        elif resolved == "global":
            reasons.append("global channel")
        signal["channel_ids"] = sorted(set(list(signal.get("channel_ids") or []) + [resolved]))
        signal["channel_match_reasons"] = reasons
        output.append(signal)
    return output, {
        "channel_id": resolved,
        "channel_label": str(definition.get("label") or resolved),
        "channel_kind": str(definition.get("kind") or "topic"),
        "region": effective_region or "",
        "country": str(country or "").strip(),
        "input_count": len(list(signals)) if isinstance(signals, list) else None,
        "matched_count": len(output),
        "silent_global_fallback": False,
    }


def _effective_feeds(channel_id: str, feeds: str | Iterable[str] | None) -> str | Iterable[str] | None:
    definition = CHANNEL_REGISTRY[channel_id]
    channel_feeds = list(definition.get("feeds") or [])
    if not channel_feeds:
        return feeds
    requested = base._normalize_feed_ids(feeds, use_defaults=False) if feeds else []
    if requested:
        return [feed_id for feed_id in requested if feed_id in channel_feeds]
    return channel_feeds


_BASE_COMPAT_NAMES = (
    "_event_signals", "_weather_signals", "_nasa_power_signals",
    "_openalex_signals", "_world_bank_signals", "_signal",
    "unified_events", "AdvancedExternalDataHub",
)
for _name in _BASE_COMPAT_NAMES:
    globals()[_name] = getattr(base, _name)


def _sync_compatibility_hooks() -> None:
    """Keep legacy monkeypatch hooks attached to the active collector namespace."""
    for name in _BASE_COMPAT_NAMES:
        setattr(base, name, globals()[name])


def build_live_intelligence(
    settings: Settings,
    *,
    category: str = "",
    limit: int = base.DEFAULT_SIGNAL_LIMIT,
    feeds: str | Iterable[str] | None = None,
    exclude: str | Iterable[str] | None = None,
    max_per_source: int = base.DEFAULT_MAX_SIGNALS_PER_SOURCE,
    record_operations: bool = True,
    channel: str = "",
    region: str = "",
    country: str = "",
) -> dict[str, Any]:
    _sync_compatibility_hooks()
    resolved = _slug(channel or "global") or "global"
    if resolved not in CHANNEL_REGISTRY:
        raise KeyError(resolved)
    definition = CHANNEL_REGISTRY[resolved]
    requested_limit = max(1, min(int(limit), base.MAX_SIGNAL_LIMIT))
    effective_category = category
    categories = list(definition.get("categories") or [])
    if not effective_category and len(categories) == 1:
        effective_category = categories[0]
    payload = base.build_live_intelligence(
        settings,
        category=effective_category,
        limit=base.MAX_SIGNAL_LIMIT,
        feeds=_effective_feeds(resolved, feeds),
        exclude=exclude,
        max_per_source=max_per_source,
        record_operations=record_operations,
    )
    filtered, diagnostics = filter_channel_signals(
        payload.get("signals") or [], channel_id=resolved, region=region, country=country,
    )
    selected = filtered[:requested_limit]
    payload = deepcopy(payload)
    payload["count"] = len(selected)
    payload["signals"] = selected
    payload["channel"] = _channel_record(resolved, definition)
    payload["channel_filter"] = diagnostics
    payload["channel_directory_url"] = "/public/live-intelligence/channels"
    payload["channel_policy_url"] = "/public/live-intelligence/channel-policy"
    payload["feed_state"]["channel"] = diagnostics
    payload["feed_state"]["useful_signal_count"] = len([item for item in selected if item.get("category") != "platform"])
    payload["feed_state"]["platform_signal_count"] = len([item for item in selected if item.get("category") == "platform"])
    payload["display"].update({
        "topic_regional_channels_supported": True,
        "country_channel_filter_supported": True,
        "channel_shortcodes_supported": True,
        "channel_registry_url": "/public/live-intelligence/channels",
    })
    payload["boundaries"] = list(payload.get("boundaries") or []) + [
        "Channel filters use explicit source metadata and do not infer missing geography from coordinates.",
        "An empty topic, region, or country channel remains empty rather than falling back to unrelated global signals.",
    ]
    return payload


def build_channel_feed(settings: Settings, channel_id: str, **kwargs: Any) -> dict[str, Any]:
    return build_live_intelligence(settings, channel=channel_id, **kwargs)


def live_intelligence_status(settings: Settings) -> dict[str, Any]:
    payload = build_live_intelligence(settings, limit=base.MAX_SIGNAL_LIMIT)
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": base.SCHEMA_VERSION,
        "signal_count": payload["count"],
        "useful_signal_count": payload["feed_state"]["useful_signal_count"],
        "generated_at": payload["generated_at"],
        "service": "available",
        "cache_safe": bool(settings.external_cache_enabled),
        "available_feeds": list(base.FEED_REGISTRY),
        "default_feeds": list(base.DEFAULT_FEEDS),
        "available_channels": list(CHANNEL_REGISTRY),
        "default_channel": "global",
        "feed_state": payload["feed_state"],
    }


def live_intelligence_ranking_policy() -> dict[str, Any]:
    return base.live_intelligence_ranking_policy()

# Compatibility exports used by earlier release modules and tests.
SCHEMA_VERSION = base.SCHEMA_VERSION
DEFAULT_SIGNAL_LIMIT = base.DEFAULT_SIGNAL_LIMIT
MAX_SIGNAL_LIMIT = base.MAX_SIGNAL_LIMIT
DEFAULT_MAX_SIGNALS_PER_SOURCE = base.DEFAULT_MAX_SIGNALS_PER_SOURCE
MAX_CONFIGURABLE_SIGNALS_PER_SOURCE = base.MAX_CONFIGURABLE_SIGNALS_PER_SOURCE
FEED_REGISTRY = base.FEED_REGISTRY
DEFAULT_FEEDS = base.DEFAULT_FEEDS
CATEGORY_LABELS = base.CATEGORY_LABELS
