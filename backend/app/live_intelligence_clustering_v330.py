"""Event clustering and transparent signal ranking for Site Intelligence v3.15.0.

The module uses deterministic, explainable heuristics. It does not infer causal
relationships, forecast event outcomes, or treat multi-source repetition as
proof that a claim is true. Clustering only reduces duplicate presentation.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from hashlib import sha256
from math import asin, cos, radians, sin, sqrt
import re
from typing import Any, Iterable, Mapping

from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-event-clustering-ranking/1.0"
DEFAULT_TIME_WINDOW_HOURS = 72
DEFAULT_DISTANCE_KM = 300
DEFAULT_TEXT_SIMILARITY = 0.34
DEFAULT_MAX_PER_SOURCE = 2

_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "near",
    "of", "on", "or", "report", "reports", "the", "to", "update", "with",
    "event", "situation", "latest", "open", "current", "new",
}
_SEVERITY_POINTS = {
    "critical": 24,
    "high": 20,
    "moderate": 14,
    "attention": 14,
    "low": 6,
    "informational": 3,
    "unknown": 2,
}
_CATEGORY_FAMILY = {
    "humanitarian": "human_crisis",
    "displacement": "human_crisis",
    "conflict": "human_crisis",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean(value: Any, limit: int = 220) -> str:
    return " ".join(str(value or "").split())[:limit]


def _tokens(record: Mapping[str, Any]) -> set[str]:
    text = " ".join([
        str(record.get("title") or ""),
        str(record.get("summary") or ""),
        str(record.get("location_label") or ""),
        str(record.get("country") or ""),
        str(record.get("country_code") or ""),
    ]).lower()
    words = re.findall(r"[a-z0-9][a-z0-9'-]{2,}", text)
    return {word for word in words if word not in _STOPWORDS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _coordinates(record: Mapping[str, Any]) -> tuple[float, float] | None:
    coords = record.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return None
    try:
        return float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None


def _distance_km(left: tuple[float, float], right: tuple[float, float]) -> float:
    lon1, lat1 = map(radians, left)
    lon2, lat2 = map(radians, right)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(a)))


def _category_family(record: Mapping[str, Any]) -> str:
    category = str(record.get("category") or "other").strip().lower()
    return _CATEGORY_FAMILY.get(category, category)


def _same_country(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_code = str(left.get("country_code") or "").strip().upper()
    right_code = str(right.get("country_code") or "").strip().upper()
    return bool(left_code and right_code and left_code == right_code)


def _event_match(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    time_window_hours: int,
    distance_km: float,
    text_similarity: float,
) -> tuple[bool, list[str]]:
    if _category_family(left) != _category_family(right):
        return False, []

    left_time = _parse_time(left.get("observed_at") or left.get("updated_at"))
    right_time = _parse_time(right.get("observed_at") or right.get("updated_at"))
    if left_time and right_time:
        hours = abs((left_time - right_time).total_seconds()) / 3600
        if hours > time_window_hours:
            return False, []
    else:
        hours = None

    reasons: list[str] = []
    left_coords = _coordinates(left)
    right_coords = _coordinates(right)
    spatial = None
    if left_coords and right_coords:
        spatial = _distance_km(left_coords, right_coords)
        if spatial <= distance_km:
            reasons.append("nearby location")

    similarity = _jaccard(_tokens(left), _tokens(right))
    if similarity >= text_similarity:
        reasons.append("matching event language")
    if _same_country(left, right):
        reasons.append("same country")
    if hours is not None and hours <= min(24, time_window_hours):
        reasons.append("close observation time")

    # Coordinates provide the strongest duplicate boundary. Without coordinates,
    # require both meaningful language overlap and a shared country/time context.
    if spatial is not None:
        matched = spatial <= distance_km and (similarity >= text_similarity * 0.55 or hours is None or hours <= 24)
    else:
        matched = similarity >= text_similarity and (_same_country(left, right) or (hours is not None and hours <= 24))
    return matched, reasons


def _record_quality(record: Mapping[str, Any]) -> tuple[float, float, float, str]:
    confidence = float(record.get("confidence") or 0.0)
    authority = {
        "official-public-source": 3.0,
        "official-public-aggregator": 2.6,
        "official-humanitarian-aggregator": 2.4,
    }.get(str((record.get("metadata") or {}).get("authority") or record.get("authority") or ""), 2.0)
    severity = float(_SEVERITY_POINTS.get(str(record.get("severity") or "unknown").lower(), 2))
    observed = _parse_time(record.get("observed_at") or record.get("updated_at"))
    timestamp = observed.timestamp() if observed else 0.0
    return confidence, authority, severity, f"{timestamp:020.4f}"


def _cluster_id(records: Iterable[Mapping[str, Any]]) -> str:
    identifiers = sorted(str(item.get("id") or item.get("source_event_id") or "") for item in records)
    digest = sha256("|".join(identifiers).encode("utf-8")).hexdigest()[:24]
    return f"sc:cluster:{digest}"


def cluster_event_records(
    records: Iterable[Mapping[str, Any]],
    *,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
    distance_km: float = DEFAULT_DISTANCE_KM,
    text_similarity: float = DEFAULT_TEXT_SIMILARITY,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return canonical event records plus public-safe clustering diagnostics."""
    time_window_hours = max(1, min(int(time_window_hours), 720))
    distance_km = max(1.0, min(float(distance_km), 2500.0))
    text_similarity = max(0.1, min(float(text_similarity), 0.95))
    ordered = [dict(item) for item in records if isinstance(item, Mapping)]
    ordered.sort(key=lambda item: str(item.get("observed_at") or item.get("updated_at") or ""), reverse=True)
    clusters: list[list[dict[str, Any]]] = []
    cluster_reasons: list[set[str]] = []

    for record in ordered:
        assigned = False
        for index, members in enumerate(clusters):
            matched, reasons = _event_match(
                record,
                members[0],
                time_window_hours=time_window_hours,
                distance_km=distance_km,
                text_similarity=text_similarity,
            )
            if matched:
                members.append(record)
                cluster_reasons[index].update(reasons)
                assigned = True
                break
        if not assigned:
            clusters.append([record])
            cluster_reasons.append(set())

    canonical: list[dict[str, Any]] = []
    for members, reasons in zip(clusters, cluster_reasons):
        selected = max(members, key=_record_quality)
        sources = sorted({str(item.get("source_name") or item.get("source") or "Public source") for item in members})
        source_urls = sorted({str(item.get("source_url") or "") for item in members if str(item.get("source_url") or "").startswith(("https://", "http://"))})
        confidences = [float(item.get("confidence") or 0.0) for item in members]
        cluster_confidence = min(0.99, max(confidences or [0.0]) + min(0.12, max(0, len(sources) - 1) * 0.04))
        row = dict(selected)
        row.update({
            "cluster_id": _cluster_id(members),
            "cluster_size": len(members),
            "cluster_source_count": len(sources),
            "corroborating_sources": sources,
            "cluster_member_ids": [str(item.get("id") or "") for item in members],
            "cluster_source_urls": source_urls,
            "cluster_confidence": round(cluster_confidence, 3),
            "cluster_reason": ", ".join(sorted(reasons)) if reasons else "single verified source record",
        })
        canonical.append(row)

    canonical.sort(key=lambda item: str(item.get("observed_at") or item.get("updated_at") or ""), reverse=True)
    source_counts = Counter(str(item.get("source_name") or item.get("source") or "Public source") for item in ordered)
    return canonical, {
        "schema": SCHEMA_VERSION,
        "version": APP_VERSION,
        "input_records": len(ordered),
        "canonical_events": len(canonical),
        "duplicates_suppressed": max(0, len(ordered) - len(canonical)),
        "multi_source_clusters": len([item for item in canonical if int(item.get("cluster_source_count") or 0) > 1]),
        "source_counts": dict(source_counts),
        "policy": {
            "time_window_hours": time_window_hours,
            "distance_km": distance_km,
            "text_similarity": text_similarity,
        },
        "boundaries": [
            "Clustering reduces duplicate presentation and is not proof that an event description is accurate.",
            "Events are never merged solely because they share a broad category.",
            "Canonical selection retains links to all represented source records when available.",
        ],
    }


def _freshness_points(signal: Mapping[str, Any], now: datetime) -> tuple[int, str]:
    observed = _parse_time(signal.get("observed_at") or signal.get("updated_at"))
    if observed is None:
        return 2, "timestamp unavailable"
    hours = max(0.0, (now - observed).total_seconds() / 3600)
    if hours <= 3:
        return 25, "observed within 3 hours"
    if hours <= 12:
        return 21, "observed within 12 hours"
    if hours <= 24:
        return 17, "observed within 24 hours"
    if hours <= 72:
        return 12, "observed within 3 days"
    if hours <= 24 * 14:
        return 7, "observed within 14 days"
    return 2, "reference or periodic data"


def _development_state(signal: Mapping[str, Any], now: datetime) -> str:
    category = str(signal.get("category") or "")
    if category in {"research", "economy_resources", "platform"}:
        return "reference"
    observed = _parse_time(signal.get("observed_at") or signal.get("updated_at"))
    hours = 99999.0 if observed is None else max(0.0, (now - observed).total_seconds() / 3600)
    sources = int(signal.get("cluster_source_count") or 1)
    if hours <= 6:
        return "new"
    if sources >= 2 or hours <= 24:
        return "developing"
    if hours <= 72:
        return "stable"
    return "continuing"


def score_signal(signal: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or _now()
    severity_name = str(signal.get("severity") or signal.get("status") or "informational").lower()
    severity = _SEVERITY_POINTS.get(severity_name, _SEVERITY_POINTS["informational"])
    freshness, freshness_reason = _freshness_points(signal, now)
    source_priority = max(1, min(int(signal.get("source_priority") or 50), 100))
    source_points = round((101 - source_priority) / 100 * 20)
    cluster_sources = max(1, int(signal.get("cluster_source_count") or 1))
    corroboration = min(15, max(0, cluster_sources - 1) * 6)
    status = str(signal.get("data_state") or signal.get("status") or "current").lower()
    penalty = -16 if status == "stale" else (-8 if status in {"degraded", "cached"} else 0)
    explicit_priority = max(0, 16 - min(16, int(signal.get("priority") or 50) // 6))
    score = max(0, min(100, severity + freshness + source_points + corroboration + explicit_priority + penalty))
    reasons = [freshness_reason]
    if severity >= 14:
        reasons.append(f"{severity_name} significance")
    if source_priority <= 25:
        reasons.append("high-priority registered source")
    if cluster_sources > 1:
        reasons.append(f"{cluster_sources} represented sources")
    if penalty:
        reasons.append(f"{status} data penalty applied")
    if explicit_priority >= 10:
        reasons.append("high editorial signal priority")
    return {
        "score": int(score),
        "reasons": reasons,
        "components": {
            "severity": severity,
            "freshness": freshness,
            "source_priority": source_points,
            "corroboration": corroboration,
            "signal_priority": explicit_priority,
            "state_penalty": penalty,
        },
        "development_state": _development_state(signal, now),
    }


def rank_signals(signals: Iterable[Mapping[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or _now()
    ranked: list[dict[str, Any]] = []
    for source in signals:
        signal = dict(source)
        ranking = score_signal(signal, now=now)
        signal["selection_score"] = ranking["score"]
        signal["selection_reasons"] = ranking["reasons"]
        signal["ranking_components"] = ranking["components"]
        signal["development_state"] = ranking["development_state"]
        ranked.append(signal)
    ranked.sort(key=lambda item: (-int(item.get("selection_score") or 0), int(item.get("priority") or 50), str(item.get("signal_id") or "")))
    return ranked


def select_ranked_signals(
    signals: Iterable[Mapping[str, Any]],
    limit: int,
    *,
    max_per_source: int = DEFAULT_MAX_PER_SOURCE,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Apply ranking, source caps, and category diversity without hiding reasons."""
    limit = max(1, int(limit))
    max_per_source = max(1, min(int(max_per_source), 5))
    seen: set[str] = set()
    source_counts: Counter[str] = Counter()
    eligible: list[dict[str, Any]] = []
    for signal in rank_signals(signals, now=now):
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        source = str(signal.get("feed_id") or signal.get("source_name") or "Unknown")
        if source_counts[source] >= max_per_source:
            continue
        source_counts[source] += 1
        eligible.append(signal)

    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()
    for signal in eligible:
        if int(signal.get("selection_score") or 0) < 70 and signal.get("severity") != "attention":
            continue
        chosen.append(signal)
        chosen_ids.add(str(signal["signal_id"]))
        if len(chosen) >= min(4, limit):
            break

    queues: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for signal in eligible:
        if str(signal.get("signal_id")) not in chosen_ids:
            queues[str(signal.get("category") or "other")].append(signal)
    order = ["earth_systems", "human_systems", "research", "economy_resources", "platform"]
    order.extend(sorted(set(queues) - set(order)))
    while len(chosen) < limit and any(queues.values()):
        progressed = False
        for category in order:
            queue = queues.get(category)
            if not queue or len(chosen) >= limit:
                continue
            chosen.append(queue.popleft())
            progressed = True
        if not progressed:
            break
    for position, signal in enumerate(chosen[:limit], start=1):
        signal["selection_rank"] = position
    return chosen[:limit]


def ranking_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA_VERSION,
        "clustering": {
            "time_window_hours": DEFAULT_TIME_WINDOW_HOURS,
            "distance_km": DEFAULT_DISTANCE_KM,
            "text_similarity": DEFAULT_TEXT_SIMILARITY,
            "category_boundary_required": True,
        },
        "ranking": {
            "maximum_score": 100,
            "components": ["severity", "freshness", "source priority", "corroboration", "signal priority", "data-state penalty"],
            "category_diversity": True,
            "source_repetition_cap": True,
            "selection_reasons_returned_per_signal": True,
        },
        "boundaries": [
            "Scores rank display relevance; they do not measure truth, danger, or institutional importance.",
            "Corroboration means multiple represented source records, not independent verification.",
            "No automated score replaces official warnings or human review.",
        ],
    }
