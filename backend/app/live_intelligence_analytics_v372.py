"""Privacy-preserving public-value analytics for Live Intelligence v3.9.0.

The analytics layer stores aggregate counters only. It rejects identity, session,
network, referrer, free-text, and full-URL fields; it never writes raw events.
Metrics are intended to measure evidence discovery, handoffs, accessibility use,
and delivery reliability rather than profile visitors or optimize for clicks alone.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import Settings
from .version import APP_VERSION

ANALYTICS_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-analytics/1.0"
MAX_BATCH_EVENTS = 25
MAX_EVENT_COUNT = 25
VALID_EVENT_TYPES = {
    "component_impression",
    "signal_impression",
    "signal_context_open",
    "source_open",
    "site_intelligence_handoff",
    "map_handoff",
    "decision_studio_handoff",
    "evidence_record_open",
    "feed_load_success",
    "feed_load_failure",
    "empty_feed",
    "reduced_motion_use",
    "manual_control_use",
}
VALID_SURFACES = {"homepage", "feed", "static_strip", "channel", "publication", "library", "advisory", "lab", "external_embed", "signal_context", "unknown"}
VALID_VIEWPORTS = {"desktop", "mobile", "tablet", "unknown"}
VALID_MOTION_MODES = {"standard", "reduced", "static", "manual", "unknown"}
VALID_DELIVERY_STATES = {
    "live", "recently_updated", "delayed", "stale", "historical", "empty", "unavailable", "unknown"
}
VALID_DESTINATIONS = {
    "signal_context", "primary_source", "site_intelligence_workspace", "evidence_record",
    "map_context", "decision_studio", "briefing", "publication", "unknown",
}
PROHIBITED_FIELDS = {
    "user_id", "user", "email", "name", "session_id", "session", "cookie", "cookies",
    "ip", "ip_address", "remote_addr", "referrer", "referer", "user_agent", "ua",
    "page_path", "page_title", "href", "url", "full_url", "query", "free_text", "metadata",
}
HANDOFF_EVENTS = {
    "signal_context_open", "source_open", "site_intelligence_handoff", "map_handoff",
    "decision_studio_handoff", "evidence_record_open",
}


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _clean(value: Any, limit: int = 160) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_key(value: Any, *, fallback: str = "unknown", limit: int = 100) -> str:
    cleaned = _clean(value, limit).lower().replace(" ", "_")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789._:-"
    cleaned = "".join(ch for ch in cleaned if ch in allowed).strip("._:-")
    return cleaned or fallback


def _bounded_count(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 1
    return max(1, min(MAX_EVENT_COUNT, parsed))


def _nested_counter() -> dict[str, Any]:
    return {
        "events": {}, "families": {}, "freshness": {}, "destinations": {},
        "viewports": {}, "motion_modes": {}, "delivery_states": {}, "sources": {}, "signals": {},
    }


def _increment(mapping: dict[str, Any], group: str, key: str, event_type: str, count: int) -> None:
    bucket = mapping.setdefault(group, {}).setdefault(key, {})
    bucket[event_type] = int(bucket.get(event_type) or 0) + count


def sanitize_analytics_event(source: Mapping[str, Any]) -> dict[str, Any]:
    prohibited = sorted(PROHIBITED_FIELDS.intersection({str(key).lower() for key in source}))
    if prohibited:
        raise ValueError("Analytics payload contains prohibited visitor or navigation fields: " + ", ".join(prohibited))
    event_type = _safe_key(source.get("event_type"), fallback="")
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError("Unsupported Live Intelligence analytics event type.")
    surface = _safe_key(source.get("surface"))
    viewport = _safe_key(source.get("viewport"))
    motion_mode = _safe_key(source.get("motion_mode"))
    delivery_state = _safe_key(source.get("delivery_state"))
    destination_type = _safe_key(source.get("destination_type"))
    return {
        "event_type": event_type,
        "count": _bounded_count(source.get("count")),
        "surface": surface if surface in VALID_SURFACES else "unknown",
        "viewport": viewport if viewport in VALID_VIEWPORTS else "unknown",
        "motion_mode": motion_mode if motion_mode in VALID_MOTION_MODES else "unknown",
        "delivery_state": delivery_state if delivery_state in VALID_DELIVERY_STATES else "unknown",
        "destination_type": destination_type if destination_type in VALID_DESTINATIONS else "unknown",
        "signal_id": _safe_key(source.get("signal_id"), fallback="", limit=180),
        "signal_family": _safe_key(source.get("signal_family"), fallback="unknown", limit=100),
        "freshness_state": _safe_key(source.get("freshness_state"), fallback="unknown", limit=60),
        "source_id": _safe_key(source.get("source_id"), fallback="unknown", limit=120),
    }


class LiveIntelligenceAnalyticsStore:
    """Atomic aggregate-only store with bounded day-level retention."""

    def __init__(self, settings: Settings):
        self.path = Path(settings.live_intelligence_analytics_state_path)
        self.retention_days = int(settings.live_intelligence_analytics_retention_days)
        self.max_signal_buckets = int(settings.live_intelligence_analytics_max_signal_buckets)

    def _empty(self) -> dict[str, Any]:
        return {"schema": ANALYTICS_SCHEMA_VERSION, "updated_at": "", "days": {}}

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return self._empty()
        if not isinstance(payload, dict):
            return self._empty()
        days = payload.get("days") if isinstance(payload.get("days"), dict) else {}
        return {
            "schema": ANALYTICS_SCHEMA_VERSION,
            "updated_at": _clean(payload.get("updated_at"), 80),
            "days": {str(key): value for key, value in days.items() if isinstance(value, dict)},
        }

    def write(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def _prune(self, state: dict[str, Any], *, now: datetime) -> None:
        cutoff = (now - timedelta(days=max(1, self.retention_days) - 1)).date().isoformat()
        state["days"] = {day: value for day, value in state.get("days", {}).items() if day >= cutoff}

    def record(self, events: Iterable[Mapping[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
        current = (now or _now_dt()).astimezone(timezone.utc)
        incoming = list(events)
        if not incoming:
            raise ValueError("At least one aggregate analytics event is required.")
        if len(incoming) > MAX_BATCH_EVENTS:
            raise ValueError(f"A maximum of {MAX_BATCH_EVENTS} analytics events may be submitted at once.")
        sanitized: list[dict[str, Any]] = []
        rejected = 0
        for item in incoming:
            if not isinstance(item, Mapping):
                rejected += 1
                continue
            try:
                sanitized.append(sanitize_analytics_event(item))
            except ValueError:
                rejected += 1
        if not sanitized:
            raise ValueError("No valid aggregate analytics events were supplied.")
        state = self.read()
        self._prune(state, now=current)
        day = current.date().isoformat()
        bucket = state.setdefault("days", {}).setdefault(day, _nested_counter())
        for event in sanitized:
            event_type = event["event_type"]
            count = event["count"]
            bucket.setdefault("events", {})[event_type] = int(bucket.get("events", {}).get(event_type) or 0) + count
            _increment(bucket, "families", event["signal_family"], event_type, count)
            _increment(bucket, "freshness", event["freshness_state"], event_type, count)
            _increment(bucket, "destinations", event["destination_type"], event_type, count)
            _increment(bucket, "viewports", event["viewport"], event_type, count)
            _increment(bucket, "motion_modes", event["motion_mode"], event_type, count)
            _increment(bucket, "delivery_states", event["delivery_state"], event_type, count)
            _increment(bucket, "sources", event["source_id"], event_type, count)
            if event["signal_id"]:
                _increment(bucket, "signals", event["signal_id"], event_type, count)
        # Bound per-signal cardinality by aggregate activity, never visitor identity.
        signal_totals = {
            key: sum(int(value or 0) for value in events_map.values())
            for key, events_map in bucket.get("signals", {}).items() if isinstance(events_map, dict)
        }
        keep = {key for key, _ in sorted(signal_totals.items(), key=lambda item: (-item[1], item[0]))[: self.max_signal_buckets]}
        bucket["signals"] = {key: value for key, value in bucket.get("signals", {}).items() if key in keep}
        state["schema"] = ANALYTICS_SCHEMA_VERSION
        state["updated_at"] = _iso(current)
        self.write(state)
        return {
            "accepted_events": len(sanitized),
            "accepted_count": sum(item["count"] for item in sanitized),
            "rejected_events": rejected,
            "stored_raw_events": False,
            "visitor_identifiers_stored": False,
            "updated_at": state["updated_at"],
        }

    def summary(self, *, days: int = 30, now: datetime | None = None, include_signals: bool = False) -> dict[str, Any]:
        current = (now or _now_dt()).astimezone(timezone.utc)
        window = max(1, min(int(days), self.retention_days))
        cutoff = (current - timedelta(days=window - 1)).date().isoformat()
        state = self.read()
        groups = _nested_counter()
        included_days = 0
        for day, bucket in sorted(state.get("days", {}).items()):
            if day < cutoff or not isinstance(bucket, dict):
                continue
            included_days += 1
            for event_type, count in (bucket.get("events") or {}).items():
                groups["events"][event_type] = int(groups["events"].get(event_type) or 0) + int(count or 0)
            for group in ("families", "freshness", "destinations", "viewports", "motion_modes", "delivery_states", "sources", "signals"):
                for key, event_counts in (bucket.get(group) or {}).items():
                    if not isinstance(event_counts, Mapping):
                        continue
                    for event_type, count in event_counts.items():
                        _increment(groups, group, str(key), str(event_type), int(count or 0))
        events = groups["events"]
        impressions = int(events.get("component_impression") or 0)
        signal_impressions = int(events.get("signal_impression") or 0)
        handoffs = sum(int(events.get(name) or 0) for name in HANDOFF_EVENTS)
        failures = int(events.get("feed_load_failure") or 0)
        successes = int(events.get("feed_load_success") or 0)
        load_total = successes + failures
        summary = {
            "ok": True,
            "version": APP_VERSION,
            "schema": ANALYTICS_SCHEMA_VERSION,
            "window_days": window,
            "included_day_count": included_days,
            "updated_at": state.get("updated_at") or "",
            "totals": deepcopy(events),
            "engagement": {
                "component_impressions": impressions,
                "signal_impressions": signal_impressions,
                "evidence_or_context_handoffs": handoffs,
                "handoffs_per_100_component_impressions": round((handoffs / impressions) * 100, 2) if impressions else 0.0,
                "source_opens": int(events.get("source_open") or 0),
                "evidence_record_opens": int(events.get("evidence_record_open") or 0),
                "decision_studio_handoffs": int(events.get("decision_studio_handoff") or 0),
                "map_handoffs": int(events.get("map_handoff") or 0),
                "site_intelligence_handoffs": int(events.get("site_intelligence_handoff") or 0),
            },
            "delivery": {
                "successful_loads": successes,
                "failed_loads": failures,
                "empty_feeds": int(events.get("empty_feed") or 0),
                "load_success_rate": round((successes / load_total) * 100, 2) if load_total else None,
            },
            "accessibility": {
                "reduced_motion_uses": int(events.get("reduced_motion_use") or 0),
                "manual_control_uses": int(events.get("manual_control_use") or 0),
            },
            "by_family": groups["families"],
            "by_freshness": groups["freshness"],
            "by_destination": groups["destinations"],
            "by_viewport": groups["viewports"],
            "by_motion_mode": groups["motion_modes"],
            "by_delivery_state": groups["delivery_states"],
            "source_reliability": build_source_reliability(groups["sources"]),
            "privacy": analytics_privacy_contract(),
        }
        if include_signals:
            summary["by_signal"] = groups["signals"]
        return summary

    def status(self) -> dict[str, Any]:
        state = self.read()
        return {
            "enabled": True,
            "day_bucket_count": len(state.get("days") or {}),
            "updated_at": state.get("updated_at") or "",
            "retention_days": self.retention_days,
            "raw_event_storage": False,
            "visitor_identifier_storage": False,
            "path_configured": bool(str(self.path)),
        }


def build_source_reliability(sources: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, counts in sources.items():
        successes = int(counts.get("feed_load_success") or 0)
        failures = int(counts.get("feed_load_failure") or 0)
        impressions = int(counts.get("signal_impression") or 0)
        opens = int(counts.get("source_open") or 0)
        total = successes + failures
        rows.append({
            "source_id": source_id,
            "signal_impressions": impressions,
            "source_opens": opens,
            "successful_loads": successes,
            "failed_loads": failures,
            "observed_load_success_rate": round((successes / total) * 100, 2) if total else None,
            "interpretation": "Aggregate client-observed delivery only; not a complete upstream service-level measure.",
        })
    return sorted(rows, key=lambda item: (-item["signal_impressions"], item["source_id"]))


def analytics_privacy_contract() -> dict[str, Any]:
    return {
        "aggregate_counters_only": True,
        "raw_events_stored": False,
        "individual_user_tracking": False,
        "cookies_required": False,
        "persistent_visitor_identifier": False,
        "ip_addresses_stored": False,
        "user_agents_stored": False,
        "referrers_stored": False,
        "page_paths_stored": False,
        "free_text_stored": False,
        "advertising_profiles": False,
        "cross_site_tracking": False,
        "optimization_target": "evidence discovery, source use, accessibility, and delivery quality—not clicks alone",
    }


def analytics_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": ANALYTICS_SCHEMA_VERSION,
        "event_types": sorted(VALID_EVENT_TYPES),
        "maximum_batch_events": MAX_BATCH_EVENTS,
        "maximum_count_per_event": MAX_EVENT_COUNT,
        "dimensions": [
            "surface", "signal_family", "freshness_state", "source_id", "destination_type",
            "viewport", "motion_mode", "delivery_state", "aggregate signal_id",
        ],
        "prohibited_fields": sorted(PROHIBITED_FIELDS),
        "privacy": analytics_privacy_contract(),
        "success_standard": [
            "Visitors reach signal context, evidence, sources, maps, workspaces, and Decision Studio.",
            "Visitors can distinguish freshness and delivery states.",
            "Reduced-motion and manual-control use are visible in aggregate.",
            "Failed and empty feeds are measurable without profiling visitors.",
            "Click-through rate is not the sole optimization target.",
        ],
        "public_summary_url": "/public/live-intelligence/analytics/summary",
        "source_reliability_url": "/public/live-intelligence/analytics/source-reliability",
    }
