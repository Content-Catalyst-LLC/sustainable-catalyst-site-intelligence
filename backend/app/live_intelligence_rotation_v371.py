"""Governed relevance and rotation selection for Live Intelligence v3.15.0.

The rotation layer operates only on public-safe, validated signals returned by the
existing reliability and gateway pipeline. It records aggregate display history,
applies deterministic diversity controls, and permits bounded human overrides.
It never changes source observations, freshness states, or represented evidence.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .config import Settings
from .version import APP_VERSION

ROTATION_SCHEMA_VERSION = "sc-site-intelligence-live-intelligence-rotation/1.0"
DEFAULT_ROTATION_WINDOW_HOURS = 168
DEFAULT_MINIMUM_DISPLAY_SECONDS = 12
DEFAULT_MAXIMUM_EXPOSURE_SECONDS = 45
MAX_PRIORITY_DELTA = 25
VALID_OVERRIDE_MODES = {"neutral", "boost", "pin", "suppress"}

FRESHNESS_POINTS = {
    "live": 25,
    "recently_updated": 21,
    "delayed": 13,
    "stale": 5,
    "historical": 8,
    "unknown": 3,
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


def _clean(value: Any, limit: int = 240) -> str:
    return " ".join(str(value or "").split())[:limit]


def _bounded_int(value: Any, minimum: int, maximum: int, fallback: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(minimum, min(maximum, parsed))


class LiveIntelligenceRotationStore:
    """Atomic public-safe store for aggregate display history and human overrides."""

    def __init__(self, settings: Settings):
        self.path = Path(settings.live_intelligence_rotation_state_path)
        self.max_history = int(settings.live_intelligence_rotation_max_history)

    def _empty(self) -> dict[str, Any]:
        return {"schema": ROTATION_SCHEMA_VERSION, "history": [], "overrides": {}}

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return self._empty()
        if not isinstance(payload, dict):
            return self._empty()
        history = payload.get("history") if isinstance(payload.get("history"), list) else []
        overrides = payload.get("overrides") if isinstance(payload.get("overrides"), dict) else {}
        return {
            "schema": ROTATION_SCHEMA_VERSION,
            "updated_at": _clean(payload.get("updated_at"), 80),
            "history": [item for item in history if isinstance(item, dict)][-self.max_history :],
            "overrides": {str(key): value for key, value in overrides.items() if isinstance(value, dict)},
        }

    def write(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def active_overrides(self, *, now: datetime | None = None) -> dict[str, dict[str, Any]]:
        current = (now or _now_dt()).astimezone(timezone.utc)
        state = self.read()
        output: dict[str, dict[str, Any]] = {}
        changed = False
        for signal_id, source in (state.get("overrides") or {}).items():
            item = dict(source)
            expires_at = _parse_timestamp(item.get("expires_at"))
            if expires_at is not None and expires_at <= current:
                changed = True
                continue
            output[signal_id] = item
        if changed:
            state["overrides"] = output
            state["updated_at"] = _iso(current)
            self.write(state)
        return output

    def exposure_counts(self, *, surface: str, window_hours: int, now: datetime | None = None) -> Counter[str]:
        current = (now or _now_dt()).astimezone(timezone.utc)
        cutoff = current - timedelta(hours=max(1, int(window_hours)))
        counts: Counter[str] = Counter()
        for record in self.read().get("history") or []:
            if str(record.get("surface") or "") != surface:
                continue
            selected_at = _parse_timestamp(record.get("selected_at"))
            if selected_at is None or selected_at < cutoff:
                continue
            for signal_id in record.get("signal_ids") or []:
                clean_id = _clean(signal_id, 180)
                if clean_id:
                    counts[clean_id] += 1
        return counts

    def record_selection(self, *, surface: str, signals: Iterable[Mapping[str, Any]], now: datetime | None = None) -> None:
        current = (now or _now_dt()).astimezone(timezone.utc)
        state = self.read()
        history = list(state.get("history") or [])
        rows = [dict(item) for item in signals]
        history.append({
            "selected_at": _iso(current),
            "surface": _clean(surface, 40),
            "signal_ids": [_clean(item.get("signal_id"), 180) for item in rows if _clean(item.get("signal_id"), 180)],
            "families": dict(Counter(_clean(item.get("signal_family") or "unknown", 80) for item in rows)),
            "sources": dict(Counter(_clean(item.get("feed_id") or item.get("source_name") or "unknown", 160) for item in rows)),
            "geographies": dict(Counter(_clean((item.get("geography") or {}).get("scope") or "global", 40) for item in rows)),
        })
        state.update({
            "schema": ROTATION_SCHEMA_VERSION,
            "updated_at": _iso(current),
            "history": history[-self.max_history :],
        })
        self.write(state)

    def set_override(self, signal_id: str, request: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
        current = (now or _now_dt()).astimezone(timezone.utc)
        clean_id = _clean(signal_id, 180)
        if not clean_id:
            raise ValueError("Signal identifier is required.")
        mode = _clean(request.get("mode") or "neutral", 20).lower()
        if mode not in VALID_OVERRIDE_MODES:
            raise ValueError("Override mode must be neutral, boost, pin, or suppress.")
        human_approved = bool(request.get("human_approved"))
        if mode != "neutral" and not human_approved:
            raise ValueError("Human approval is required for a visibility or priority override.")
        priority_delta = _bounded_int(request.get("priority_delta"), -MAX_PRIORITY_DELTA, MAX_PRIORITY_DELTA, 0)
        if mode == "boost" and priority_delta == 0:
            priority_delta = 10
        expires_at = _parse_timestamp(request.get("expires_at"))
        if expires_at is not None and expires_at <= current:
            raise ValueError("Override expiry must be in the future.")
        reason = _clean(request.get("reason"), 320)
        if mode != "neutral" and not reason:
            raise ValueError("A public-interest reason is required for an override.")
        state = self.read()
        overrides = dict(state.get("overrides") or {})
        if mode == "neutral":
            overrides.pop(clean_id, None)
            result = {"signal_id": clean_id, "mode": "neutral", "active": False}
        else:
            result = {
                "signal_id": clean_id,
                "mode": mode,
                "priority_delta": priority_delta,
                "reason": reason,
                "human_approved": True,
                "updated_at": _iso(current),
                "updated_by": _clean(request.get("updated_by") or "authorized administrator", 120),
                "expires_at": _iso(expires_at) if expires_at else "",
                "changes_observation": False,
                "automatic_emergency_publication": False,
                "active": True,
            }
            overrides[clean_id] = result
        state.update({"schema": ROTATION_SCHEMA_VERSION, "updated_at": _iso(current), "overrides": overrides})
        self.write(state)
        return result

    def status(self, *, now: datetime | None = None) -> dict[str, Any]:
        state = self.read()
        overrides = self.active_overrides(now=now)
        history = state.get("history") or []
        return {
            "enabled": True,
            "history_record_count": len(history),
            "active_override_count": len(overrides),
            "updated_at": _clean(state.get("updated_at"), 80),
            "path_configured": bool(str(self.path)),
        }


def _source_health_points(signal: Mapping[str, Any]) -> tuple[int, str]:
    if str(signal.get("validation_state") or "valid") != "valid":
        return 0, "signal validation did not pass"
    data_state = str(signal.get("data_state") or signal.get("status") or "current").lower()
    if data_state in {"error", "unavailable", "failed"}:
        return 0, "source unavailable"
    if data_state == "stale":
        return 8, "source delivered stale data"
    if data_state in {"cached", "degraded"}:
        return 13, "source delivered cached or degraded data"
    if signal.get("source_url"):
        return 20, "validated signal with a traceable source"
    return 15, "validated signal with limited source navigation"


def _public_relevance_points(signal: Mapping[str, Any]) -> tuple[int, list[str]]:
    points = 0
    reasons: list[str] = []
    if signal.get("primary_destination"):
        points += 6
        reasons.append("useful next step available")
    if signal.get("signal_family"):
        points += 4
    geography = signal.get("geography") or {}
    if geography.get("label"):
        points += 3
    if signal.get("methodology_note") and signal.get("responsible_use_note"):
        points += 4
        reasons.append("method and responsible-use context available")
    if signal.get("evidence_url") or any(
        str(item.get("type") or "") == "evidence_record"
        for item in (signal.get("secondary_destinations") or []) if isinstance(item, Mapping)
    ):
        points += 3
        reasons.append("evidence handoff available")
    return min(20, points), reasons


def score_rotation_candidate(
    signal: Mapping[str, Any],
    *,
    exposure_count: int = 0,
    override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    item = deepcopy(dict(signal))
    override = dict(override or {})
    freshness_state = str(item.get("freshness_state") or "unknown")
    freshness = FRESHNESS_POINTS.get(freshness_state, FRESHNESS_POINTS["unknown"])
    source_health, source_reason = _source_health_points(item)
    public_relevance, relevance_reasons = _public_relevance_points(item)
    base_ranking = _bounded_int(round(float(item.get("selection_score") or item.get("priority_score") or 0) / 5), 0, 20, 0)
    editorial_priority = _bounded_int(20 - int(item.get("priority") or 50) // 5, 0, 20, 0)
    repetition_penalty = min(25, max(0, int(exposure_count)) * 5)
    priority_delta = _bounded_int(override.get("priority_delta"), -MAX_PRIORITY_DELTA, MAX_PRIORITY_DELTA, 0)
    pinned = str(override.get("mode") or "") == "pin"
    suppressed = str(override.get("mode") or "") == "suppress"
    score = freshness + source_health + public_relevance + base_ranking + editorial_priority + priority_delta - repetition_penalty
    if pinned:
        score += 1000
    reasons = [
        f"{freshness_state.replace('_', ' ')} freshness",
        source_reason,
        *relevance_reasons,
    ]
    if base_ranking >= 14:
        reasons.append("strong underlying relevance rank")
    if exposure_count:
        reasons.append(f"shown {exposure_count} time{'s' if exposure_count != 1 else ''} in the rotation window")
    if priority_delta:
        reasons.append("human-approved priority adjustment")
    if pinned:
        reasons.append("human-approved pinned selection")
    if suppressed:
        reasons.append("human-approved suppression")
    item.update({
        "rotation_base_score": int(score),
        "rotation_score": int(score),
        "rotation_score_components": {
            "freshness": freshness,
            "source_health": source_health,
            "public_relevance": public_relevance,
            "underlying_rank": base_ranking,
            "editorial_priority": editorial_priority,
            "human_priority_delta": priority_delta,
            "repetition_penalty": -repetition_penalty,
            "pin_bonus": 1000 if pinned else 0,
        },
        "rotation_reasons": reasons,
        "rotation_exposure_count": int(exposure_count),
        "rotation_override": {
            "mode": str(override.get("mode") or "neutral"),
            "active": bool(override),
            "human_approved": bool(override.get("human_approved")),
            "reason": _clean(override.get("reason"), 320),
            "expires_at": _clean(override.get("expires_at"), 80),
        },
        "rotation_eligible": not suppressed and bool(item.get("homepage_eligible", True)),
    })
    return item


def select_rotation_signals(
    signals: Iterable[Mapping[str, Any]],
    *,
    limit: int,
    exposure_counts: Mapping[str, int] | None = None,
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested_limit = max(1, int(limit))
    exposure_counts = exposure_counts or {}
    overrides = overrides or {}
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    suppressed_ids: list[str] = []
    for source in signals:
        if not isinstance(source, Mapping):
            continue
        signal_id = _clean(source.get("signal_id"), 180)
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        scored = score_rotation_candidate(
            source,
            exposure_count=int(exposure_counts.get(signal_id, 0) or 0),
            override=overrides.get(signal_id),
        )
        if not scored["rotation_eligible"]:
            suppressed_ids.append(signal_id)
            continue
        candidates.append(scored)

    candidates.sort(key=lambda item: (
        -int(item.get("rotation_base_score") or 0),
        int(item.get("priority") or 50),
        str(item.get("signal_id") or ""),
    ))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    family_counts: Counter[str] = Counter()
    geography_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    remaining = list(candidates)

    while remaining and len(selected) < requested_limit:
        best_index = 0
        best_key: tuple[int, int, int] | None = None
        best_signal_id = ""
        best_adjustments: dict[str, int] = {}
        for index, candidate in enumerate(remaining):
            family = _clean(candidate.get("signal_family") or "unknown", 80)
            geography = _clean((candidate.get("geography") or {}).get("scope") or "global", 40)
            source = _clean(candidate.get("feed_id") or candidate.get("source_name") or "unknown", 160)
            family_adjustment = 12 if family_counts[family] == 0 else -min(12, family_counts[family] * 4)
            geography_adjustment = 6 if geography_counts[geography] == 0 else -min(6, geography_counts[geography] * 2)
            source_adjustment = 4 if source_counts[source] == 0 else -min(12, source_counts[source] * 4)
            adjusted = int(candidate.get("rotation_base_score") or 0) + family_adjustment + geography_adjustment + source_adjustment
            candidate_id = str(candidate.get("signal_id") or "")
            key = (adjusted, int(candidate.get("selection_score") or 0), -int(candidate.get("priority") or 50))
            if best_key is None or key > best_key or (key == best_key and candidate_id < best_signal_id):
                best_key = key
                best_signal_id = candidate_id
                best_index = index
                best_adjustments = {
                    "family_diversity": family_adjustment,
                    "geography_diversity": geography_adjustment,
                    "source_diversity": source_adjustment,
                }
        chosen = remaining.pop(best_index)
        signal_id = str(chosen.get("signal_id") or "")
        if signal_id in selected_ids:
            continue
        chosen["rotation_diversity_adjustments"] = best_adjustments
        chosen["rotation_score"] = int(chosen.get("rotation_base_score") or 0) + sum(best_adjustments.values())
        chosen["rotation_reasons"] = list(chosen.get("rotation_reasons") or []) + [
            "family diversity bonus" if best_adjustments["family_diversity"] > 0 else "family repetition adjustment",
            "source diversity bonus" if best_adjustments["source_diversity"] > 0 else "source repetition adjustment",
        ]
        selected.append(chosen)
        selected_ids.add(signal_id)
        family_counts[_clean(chosen.get("signal_family") or "unknown", 80)] += 1
        geography_counts[_clean((chosen.get("geography") or {}).get("scope") or "global", 40)] += 1
        source_counts[_clean(chosen.get("feed_id") or chosen.get("source_name") or "unknown", 160)] += 1

    for index, signal in enumerate(selected, start=1):
        signal["rotation_rank"] = index
        signal["minimum_display_seconds"] = DEFAULT_MINIMUM_DISPLAY_SECONDS
        signal["maximum_continuous_exposure_seconds"] = DEFAULT_MAXIMUM_EXPOSURE_SECONDS

    return selected, {
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "suppressed_count": len(suppressed_ids),
        "suppressed_signal_ids": suppressed_ids,
        "family_counts": dict(family_counts),
        "geography_counts": dict(geography_counts),
        "source_counts": dict(source_counts),
        "deterministic_fallback_order": [str(item.get("signal_id") or "") for item in candidates],
    }


def apply_rotation_policy(
    payload: Mapping[str, Any],
    settings: Settings,
    *,
    limit: int,
    surface: str = "homepage",
    record_history: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = (now or _now_dt()).astimezone(timezone.utc)
    result = deepcopy(dict(payload))
    if not bool(settings.live_intelligence_rotation_enabled):
        result["signals"] = list(result.get("signals") or [])[: max(1, int(limit))]
        result["count"] = len(result["signals"])
        return result

    store = LiveIntelligenceRotationStore(settings)
    window_hours = int(settings.live_intelligence_rotation_window_hours)
    exposures = store.exposure_counts(surface=surface, window_hours=window_hours, now=current)
    overrides = store.active_overrides(now=current)
    selected, diagnostics = select_rotation_signals(
        result.get("signals") or [],
        limit=limit,
        exposure_counts=exposures,
        overrides=overrides,
    )
    minimum_display = int(settings.live_intelligence_minimum_display_seconds)
    maximum_exposure = max(minimum_display, int(settings.live_intelligence_maximum_exposure_seconds))
    for signal in selected:
        signal["minimum_display_seconds"] = minimum_display
        signal["maximum_continuous_exposure_seconds"] = maximum_exposure
    result["signals"] = selected
    result["count"] = len(selected)
    result["rotation_schema"] = ROTATION_SCHEMA_VERSION
    result["rotation"] = {
        "surface": surface,
        "selected_at": _iso(current),
        "window_hours": window_hours,
        "minimum_display_seconds": minimum_display,
        "maximum_continuous_exposure_seconds": maximum_exposure,
        "active_override_count": len(overrides),
        "history_recording": bool(record_history),
        "anonymous_aggregate_history_only": True,
        **diagnostics,
    }
    display = dict(result.get("display") or {})
    display.update({
        "governed_rotation_supported": True,
        "transparent_rotation_scores_supported": True,
        "family_geography_source_diversity_supported": True,
        "aggregate_rotation_history_supported": True,
        "human_controlled_overrides_supported": True,
        "automatic_emergency_publication": False,
    })
    result["display"] = display
    feed_state = dict(result.get("feed_state") or {})
    feed_state["rotation"] = {
        "candidate_count": diagnostics["candidate_count"],
        "selected_count": diagnostics["selected_count"],
        "suppressed_count": diagnostics["suppressed_count"],
        "active_override_count": len(overrides),
    }
    result["feed_state"] = feed_state
    boundaries = list(result.get("boundaries") or [])
    for boundary in (
        "Rotation scores order public display relevance; they do not measure truth, danger, or social importance.",
        "Display history is aggregate signal exposure history and does not profile individual visitors.",
        "Human overrides can change visibility or priority but cannot change source observations, evidence, or freshness.",
        "High-impact or emergency claims are never published automatically by the rotation engine.",
    ):
        if boundary not in boundaries:
            boundaries.append(boundary)
    result["boundaries"] = boundaries
    if record_history and selected:
        store.record_selection(surface=surface, signals=selected, now=current)
    return result


def rotation_policy() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": ROTATION_SCHEMA_VERSION,
        "name": "Live Intelligence Relevance and Rotation Policy",
        "score_components": [
            "freshness", "source health", "public relevance", "underlying relevance rank",
            "editorial priority", "family diversity", "geography diversity", "source diversity",
            "repetition penalty", "bounded human priority adjustment",
        ],
        "rotation_window_hours": DEFAULT_ROTATION_WINDOW_HOURS,
        "minimum_display_seconds": DEFAULT_MINIMUM_DISPLAY_SECONDS,
        "maximum_continuous_exposure_seconds": DEFAULT_MAXIMUM_EXPOSURE_SECONDS,
        "maximum_priority_delta": MAX_PRIORITY_DELTA,
        "override_modes": sorted(VALID_OVERRIDE_MODES),
        "deterministic_fallback": True,
        "selection_reasons_returned_per_signal": True,
        "history": {
            "aggregate_signal_exposure_only": True,
            "individual_user_tracking": False,
            "visitor_profile_creation": False,
        },
        "governance": {
            "human_approval_required_for_override": True,
            "automatic_emergency_publication": False,
            "override_changes_observation": False,
            "expired_overrides_removed_automatically": True,
        },
        "boundaries": [
            "Scores rank display relevance, not factual certainty or emergency severity.",
            "Diversity adjustments prevent accidental domination; they do not create false equivalence.",
            "A pin or boost is an inspectable editorial decision and never rewrites the represented source.",
        ],
    }
