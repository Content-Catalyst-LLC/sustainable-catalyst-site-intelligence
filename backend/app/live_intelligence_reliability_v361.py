"""Reliability, freshness, and last-known-good delivery for Live Intelligence.

Site Intelligence v3.7.2 keeps the v3.5.0 channel and ranking engine intact and
adds a public-safe reliability boundary around it. The boundary validates each
signal, assigns explicit freshness states, suppresses expired observations, and
recovers only from a last-known-good payload created for the same query.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import Settings
from .version import APP_VERSION
from . import live_intelligence_channels_v350 as base
from .live_intelligence_gateway_v370 import apply_gateway_policy

RELIABILITY_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-reliability/1.0"
VALID_FRESHNESS_STATES = {
    "live", "recently_updated", "delayed", "stale", "historical", "unknown"
}


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_text(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_url(value: Any) -> str:
    url = str(value or "").strip()
    if not url:
        return ""
    if url.startswith(("https://", "http://", "/")):
        return url[:1200]
    return ""


def _query_key(parameters: Mapping[str, Any]) -> str:
    normalized = json.dumps(parameters, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class LiveIntelligenceReliabilityStore:
    """Small atomic JSON store for same-query last-known-good payloads."""

    def __init__(self, settings: Settings):
        self.path = Path(settings.live_intelligence_last_known_good_path)
        self.max_entries = int(settings.live_intelligence_last_known_good_max_entries)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema": RELIABILITY_SCHEMA_VERSION, "entries": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return {"schema": RELIABILITY_SCHEMA_VERSION, "entries": {}}
        if not isinstance(payload, dict) or not isinstance(payload.get("entries"), dict):
            return {"schema": RELIABILITY_SCHEMA_VERSION, "entries": {}}
        return payload

    def _write(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def get(self, key: str, retention_hours: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        state = self._read()
        entry = (state.get("entries") or {}).get(key)
        if not isinstance(entry, dict) or not isinstance(entry.get("payload"), dict):
            return None, {"available": False, "reason": "missing"}
        saved_at = _parse_timestamp(entry.get("saved_at"))
        if saved_at is None:
            return None, {"available": False, "reason": "invalid_timestamp"}
        age_seconds = max(0, int((_now_dt() - saved_at).total_seconds()))
        if age_seconds > max(1, int(retention_hours)) * 3600:
            return None, {"available": False, "reason": "expired", "age_seconds": age_seconds}
        return deepcopy(entry["payload"]), {
            "available": True,
            "saved_at": _iso(saved_at),
            "age_seconds": age_seconds,
            "signal_count": int(entry.get("signal_count") or len(entry["payload"].get("signals") or [])),
        }

    def put(self, key: str, payload: Mapping[str, Any]) -> None:
        state = self._read()
        entries = dict(state.get("entries") or {})
        entries[key] = {
            "saved_at": _iso(_now_dt()),
            "signal_count": len(payload.get("signals") or []),
            "payload": deepcopy(dict(payload)),
        }
        ordered = sorted(
            entries.items(),
            key=lambda item: str((item[1] or {}).get("saved_at") or ""),
            reverse=True,
        )[: self.max_entries]
        self._write({
            "schema": RELIABILITY_SCHEMA_VERSION,
            "updated_at": _iso(_now_dt()),
            "entries": dict(ordered),
        })

    def status(self) -> dict[str, Any]:
        state = self._read()
        entries = state.get("entries") or {}
        return {
            "enabled": True,
            "entry_count": len(entries),
            "updated_at": str(state.get("updated_at") or ""),
            "path_configured": bool(str(self.path)),
        }


def classify_signal_freshness(signal: Mapping[str, Any], settings: Settings, *, now: datetime | None = None) -> dict[str, Any]:
    now = (now or _now_dt()).astimezone(timezone.utc)
    data_state = str(signal.get("data_state") or signal.get("status") or "").strip().lower()
    observed = _parse_timestamp(signal.get("observed_at"))
    updated = _parse_timestamp(signal.get("updated_at"))
    timestamp = observed or updated

    if data_state in {"historical", "periodic", "archived"}:
        state = "historical"
    elif timestamp is None:
        state = "unknown"
    else:
        age_seconds = max(0, int((now - timestamp).total_seconds()))
        fresh_seconds = int(settings.live_intelligence_fresh_minutes) * 60
        delayed_seconds = int(settings.live_intelligence_delayed_hours) * 3600
        stale_seconds = int(settings.live_intelligence_stale_hours) * 3600
        if data_state == "stale" or age_seconds > stale_seconds:
            state = "stale"
        elif age_seconds > delayed_seconds:
            state = "delayed"
        elif age_seconds > fresh_seconds:
            state = "recently_updated"
        else:
            state = "live"

    age_seconds = None if timestamp is None else max(0, int((now - timestamp).total_seconds()))
    labels = {
        "live": "Live",
        "recently_updated": "Recently updated",
        "delayed": "Delayed",
        "stale": "Stale",
        "historical": "Historical observation",
        "unknown": "Update time unavailable",
    }
    return {
        "state": state,
        "label": labels[state],
        "age_seconds": age_seconds,
        "timestamp": _iso(timestamp) if timestamp else "",
    }


def _validate_signal(signal: Mapping[str, Any], settings: Settings, *, now: datetime) -> tuple[dict[str, Any] | None, str]:
    signal_id = _safe_text(signal.get("signal_id"), 180)
    label = _safe_text(signal.get("label"), 120)
    value = _safe_text(signal.get("value"), 220)
    source_name = _safe_text(signal.get("source_name"), 160)
    if not signal_id:
        return None, "missing_signal_id"
    if not label:
        return None, "missing_label"
    if not value:
        return None, "missing_value"
    if not source_name:
        return None, "missing_source"

    item = deepcopy(dict(signal))
    item["signal_id"] = signal_id
    item["label"] = label
    item["value"] = value
    item["source_name"] = source_name
    item["source_short_name"] = _safe_text(item.get("source_short_name") or source_name, 64)
    item["source_url"] = _safe_url(item.get("source_url"))
    item["destination_url"] = _safe_url(item.get("destination_url"))
    item["context_view_url"] = _safe_url(item.get("context_view_url"))
    item["detail"] = _safe_text(item.get("detail"), 560)
    item["category"] = _safe_text(item.get("category") or "signal", 80)
    item["status"] = _safe_text(item.get("status") or "current", 40)
    item["data_state"] = _safe_text(item.get("data_state") or item["status"], 60)

    freshness = classify_signal_freshness(item, settings, now=now)
    item["freshness_state"] = freshness["state"]
    item["freshness_label"] = freshness["label"]
    item["freshness_age_seconds"] = freshness["age_seconds"]
    item["freshness_timestamp"] = freshness["timestamp"]
    item["validation_state"] = "valid"

    maximum_age = int(settings.live_intelligence_max_signal_age_hours) * 3600
    if (
        bool(settings.live_intelligence_suppress_expired_signals)
        and freshness["age_seconds"] is not None
        and freshness["age_seconds"] > maximum_age
        and freshness["state"] != "historical"
    ):
        return None, "expired"
    return item, "valid"


def apply_reliability_policy(payload: Mapping[str, Any], settings: Settings, *, now: datetime | None = None) -> dict[str, Any]:
    now = (now or _now_dt()).astimezone(timezone.utc)
    result = deepcopy(dict(payload))
    raw_signals = payload.get("signals") if isinstance(payload.get("signals"), list) else []
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    rejection_counts: dict[str, int] = {}

    for source_signal in raw_signals:
        if not isinstance(source_signal, Mapping):
            rejection_counts["invalid_type"] = rejection_counts.get("invalid_type", 0) + 1
            continue
        signal, reason = _validate_signal(source_signal, settings, now=now)
        if signal is None:
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
            continue
        if signal["signal_id"] in seen:
            rejection_counts["duplicate_signal_id"] = rejection_counts.get("duplicate_signal_id", 0) + 1
            continue
        seen.add(signal["signal_id"])
        selected.append(signal)

    freshness_counts: dict[str, int] = {}
    for signal in selected:
        state = str(signal.get("freshness_state") or "unknown")
        freshness_counts[state] = freshness_counts.get(state, 0) + 1

    if not selected:
        delivery_state = "empty"
    elif freshness_counts.get("live"):
        delivery_state = "live"
    elif freshness_counts.get("recently_updated"):
        delivery_state = "recently_updated"
    elif freshness_counts.get("delayed"):
        delivery_state = "delayed"
    elif freshness_counts.get("stale"):
        delivery_state = "stale"
    else:
        delivery_state = "historical"

    result["signals"] = selected
    result["count"] = len(selected)
    result["schema"] = str(result.get("schema") or base.SCHEMA_VERSION)
    result["reliability_schema"] = RELIABILITY_SCHEMA_VERSION
    result["delivery"] = {
        "state": delivery_state,
        "label": delivery_state.replace("_", " ").title(),
        "generated_at": str(result.get("generated_at") or _iso(now)),
        "served_at": _iso(now),
        "last_known_good": False,
        "cache_age_seconds": 0,
    }
    feed_state = dict(result.get("feed_state") or {})
    feed_state["reliability"] = {
        "input_signal_count": len(raw_signals),
        "valid_signal_count": len(selected),
        "rejected_signal_count": sum(rejection_counts.values()),
        "rejection_counts": rejection_counts,
        "freshness_counts": freshness_counts,
        "expired_signals_suppressed": rejection_counts.get("expired", 0),
        "duplicate_signals_suppressed": rejection_counts.get("duplicate_signal_id", 0),
        "partial_feed": bool(selected) and len(selected) < len(raw_signals),
    }
    result["feed_state"] = feed_state
    display = dict(result.get("display") or {})
    display.update({
        "explicit_freshness_states_supported": True,
        "last_known_good_delivery_supported": True,
        "malformed_signal_isolation_supported": True,
        "expired_signal_suppression_supported": True,
        "partial_feed_rendering_supported": True,
    })
    result["display"] = display
    result["boundaries"] = list(result.get("boundaries") or []) + [
        "A cached payload is reused only for the same channel, geography, source selection, and limit query.",
        "Expired or malformed signals are withheld rather than converted to zero or fabricated replacement values.",
        "Freshness labels describe delivery timing and do not certify accuracy, importance, or completeness.",
    ]
    return result


def _origin_failed(payload: Mapping[str, Any]) -> bool:
    if payload.get("ok") is False:
        return True
    feed_state = payload.get("feed_state") or {}
    if not isinstance(feed_state, Mapping):
        return False
    if payload.get("signals"):
        return False
    channel = payload.get("channel_filter") or {}
    if isinstance(channel, Mapping) and int(channel.get("matched_count") or 0) == 0 and (
        str(channel.get("country") or "") or str(channel.get("region") or "") or str(channel.get("channel_id") or "global") != "global"
    ):
        return False
    states: list[str] = []
    for value in feed_state.values():
        if isinstance(value, Mapping):
            state = str(value.get("data_state") or value.get("state") or "").lower()
            if state:
                states.append(state)
    return bool(states) and all(state in {"unavailable", "error", "failed", "live-disabled", "empty"} for state in states)


def _parameters(
    *, category: str, limit: int, feeds: str | Iterable[str] | None,
    exclude: str | Iterable[str] | None, max_per_source: int,
    channel: str, region: str, country: str,
) -> dict[str, Any]:
    def normalized(value: str | Iterable[str] | None) -> list[str] | str:
        if value is None:
            return ""
        if isinstance(value, str):
            return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return [str(part).strip() for part in value if str(part).strip()]
    return {
        "category": str(category or ""),
        "limit": int(limit),
        "feeds": normalized(feeds),
        "exclude": normalized(exclude),
        "max_per_source": int(max_per_source),
        "channel": str(channel or "global"),
        "region": str(region or ""),
        "country": str(country or ""),
    }


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
    if not bool(settings.live_intelligence_reliability_enabled):
        return apply_gateway_policy(base.build_live_intelligence(
            settings, category=category, limit=limit, feeds=feeds, exclude=exclude,
            max_per_source=max_per_source, record_operations=record_operations,
            channel=channel, region=region, country=country,
        ))

    parameters = _parameters(
        category=category, limit=limit, feeds=feeds, exclude=exclude,
        max_per_source=max_per_source, channel=channel, region=region, country=country,
    )
    key = _query_key(parameters)
    store = LiveIntelligenceReliabilityStore(settings)
    origin_error = ""
    try:
        payload = base.build_live_intelligence(
            settings, category=category, limit=limit, feeds=feeds, exclude=exclude,
            max_per_source=max_per_source, record_operations=record_operations,
            channel=channel, region=region, country=country,
        )
        reliable = apply_reliability_policy(payload, settings)
        if not _origin_failed(reliable):
            if reliable.get("signals"):
                store.put(key, reliable)
            reliable["delivery"]["query_fingerprint"] = key[:16]
            reliable["delivery"]["origin"] = "current_request"
            return apply_gateway_policy(reliable)
        origin_error = "origin_returned_no_usable_signals"
    except KeyError:
        raise
    except Exception as exc:  # individual connector details remain internal
        origin_error = exc.__class__.__name__

    cached, cache_meta = store.get(key, int(settings.live_intelligence_last_known_good_retention_hours))
    if cached is not None:
        recovered = apply_reliability_policy(cached, settings)
        recovered["generated_at"] = str(cached.get("generated_at") or recovered.get("generated_at") or "")
        recovered["delivery"].update({
            "state": "delayed",
            "label": "Delayed — last verified signals",
            "last_known_good": True,
            "cache_age_seconds": int(cache_meta.get("age_seconds") or 0),
            "cached_at": str(cache_meta.get("saved_at") or ""),
            "origin": "last_known_good",
            "origin_error": origin_error,
            "query_fingerprint": key[:16],
        })
        recovered["ok"] = True
        recovered["feed_state"]["reliability"]["recovered_from_last_known_good"] = True
        return apply_gateway_policy(recovered)

    empty = {
        "ok": True,
        "version": APP_VERSION,
        "schema": base.SCHEMA_VERSION,
        "reliability_schema": RELIABILITY_SCHEMA_VERSION,
        "generated_at": _iso(_now_dt()),
        "category": category or "all",
        "count": 0,
        "signals": [],
        "feeds": [],
        "feed_state": {
            "reliability": {
                "input_signal_count": 0,
                "valid_signal_count": 0,
                "rejected_signal_count": 0,
                "rejection_counts": {},
                "freshness_counts": {},
                "partial_feed": False,
                "recovered_from_last_known_good": False,
            }
        },
        "display": {
            "label": "Live Intelligence",
            "explicit_freshness_states_supported": True,
            "last_known_good_delivery_supported": True,
            "malformed_signal_isolation_supported": True,
        },
        "delivery": {
            "state": "unavailable",
            "label": "Temporarily unavailable",
            "generated_at": _iso(_now_dt()),
            "served_at": _iso(_now_dt()),
            "last_known_good": False,
            "cache_age_seconds": 0,
            "origin": "unavailable",
            "origin_error": origin_error,
            "query_fingerprint": key[:16],
        },
        "boundaries": [
            "No signal values are fabricated when current and same-query last-known-good data are unavailable."
        ],
    }
    return apply_gateway_policy(empty)


def build_channel_feed(settings: Settings, channel_id: str, **kwargs: Any) -> dict[str, Any]:
    return build_live_intelligence(settings, channel=channel_id, **kwargs)


def live_intelligence_status(settings: Settings) -> dict[str, Any]:
    payload = build_live_intelligence(settings, limit=base.MAX_SIGNAL_LIMIT)
    reliability = payload.get("feed_state", {}).get("reliability", {})
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": RELIABILITY_SCHEMA_VERSION,
        "service": "available" if payload.get("delivery", {}).get("state") != "unavailable" else "degraded",
        "signal_count": int(payload.get("count") or 0),
        "useful_signal_count": len([item for item in payload.get("signals") or [] if item.get("category") != "platform"]),
        "generated_at": str(payload.get("generated_at") or ""),
        "delivery": payload.get("delivery") or {},
        "freshness_counts": reliability.get("freshness_counts") or {},
        "rejected_signal_count": int(reliability.get("rejected_signal_count") or 0),
        "partial_feed": bool(reliability.get("partial_feed")),
        "cache_safe": bool(settings.external_cache_enabled),
        "last_known_good": LiveIntelligenceReliabilityStore(settings).status(),
        "available_feeds": list(base.FEED_REGISTRY),
        "default_feeds": list(base.DEFAULT_FEEDS),
        "available_channels": list(base.CHANNEL_REGISTRY),
        "default_channel": "global",
        "thresholds": {
            "fresh_minutes": int(settings.live_intelligence_fresh_minutes),
            "delayed_hours": int(settings.live_intelligence_delayed_hours),
            "stale_hours": int(settings.live_intelligence_stale_hours),
            "maximum_signal_age_hours": int(settings.live_intelligence_max_signal_age_hours),
            "last_known_good_retention_hours": int(settings.live_intelligence_last_known_good_retention_hours),
        },
    }


def live_intelligence_ranking_policy() -> dict[str, Any]:
    return base.live_intelligence_ranking_policy()


def channel_directory() -> dict[str, Any]:
    return base.channel_directory()


def channel_definition(channel_id: str) -> dict[str, Any]:
    return base.channel_definition(channel_id)


def channel_policy() -> dict[str, Any]:
    return base.channel_policy()


# Compatibility exports used by the API and earlier release tests.
SCHEMA_VERSION = base.SCHEMA_VERSION
DEFAULT_SIGNAL_LIMIT = base.DEFAULT_SIGNAL_LIMIT
MAX_SIGNAL_LIMIT = base.MAX_SIGNAL_LIMIT
DEFAULT_MAX_SIGNALS_PER_SOURCE = base.DEFAULT_MAX_SIGNALS_PER_SOURCE
MAX_CONFIGURABLE_SIGNALS_PER_SOURCE = base.MAX_CONFIGURABLE_SIGNALS_PER_SOURCE
FEED_REGISTRY = base.FEED_REGISTRY
DEFAULT_FEEDS = base.DEFAULT_FEEDS
CATEGORY_LABELS = base.CATEGORY_LABELS
CHANNEL_REGISTRY = base.CHANNEL_REGISTRY
