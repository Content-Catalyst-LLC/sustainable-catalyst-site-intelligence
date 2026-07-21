"""Live Intelligence source operations for Site Intelligence v3.15.0.

This module provides a public-safe source registry and a protected operational
control plane for the electronic Live Intelligence board. Runtime state is
file-backed so deployments can redirect it to persistent storage without
placing credentials, request headers, or complete upstream payloads in the
release repository.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any, Callable, Iterable, Mapping

from .config import Settings
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-live-source-operations/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-live-source-registry/1.0"
_LOCK = threading.RLock()
_ALLOWED_STATES = {"live", "cached", "stale", "current", "empty", "disabled", "unavailable", "error", "live-disabled", "fallback-suppressed"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    repository_root = Path(__file__).resolve().parents[2]
    candidate = repository_root / path
    if candidate.exists() or str(path).startswith("backend/"):
        return candidate
    return path


def _read_json(path: Path, default: Mapping[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return deepcopy(dict(default))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return deepcopy(dict(default))
    return payload if isinstance(payload, dict) else deepcopy(dict(default))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return []
    return rows[-max(1, min(int(limit), 1000)):]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


class LiveIntelligenceSourceOperations:
    """Public-safe registry plus protected source health and test operations."""

    def __init__(self, settings: Settings, *, now_fn: Callable[[], datetime] = _now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.registry_path = _resolve_path(settings.live_source_operations_registry_path)
        self.state_path = _resolve_path(settings.live_source_operations_state_path)
        self.history_path = _resolve_path(settings.live_source_operations_history_path)
        self._registry = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        payload = _read_json(self.registry_path, {})
        if payload.get("schema") != REGISTRY_SCHEMA:
            raise ValueError(f"Invalid Live Intelligence source registry schema at {self.registry_path}")
        sources = payload.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("Live Intelligence source registry must contain sources.")
        identifiers = [str(item.get("feed_id") or "") for item in sources if isinstance(item, dict)]
        if not all(identifiers) or len(identifiers) != len(set(identifiers)):
            raise ValueError("Live Intelligence source IDs must be unique non-empty strings.")
        return payload

    def _default_state(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "version": APP_VERSION,
            "updated_at": _iso(self.now_fn()),
            "sources": {},
        }

    def _state(self) -> dict[str, Any]:
        state = _read_json(self.state_path, self._default_state())
        state.setdefault("sources", {})
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        state["schema"] = SCHEMA_VERSION
        state["version"] = APP_VERSION
        state["updated_at"] = _iso(self.now_fn())
        _write_json(self.state_path, state)

    def _source_map(self) -> dict[str, dict[str, Any]]:
        return {str(item["feed_id"]): item for item in self._registry["sources"]}

    def _effective(self, source: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "enabled": _bool(runtime.get("enabled", source.get("default_enabled", True))),
            "priority": _bounded_int(runtime.get("priority", source.get("default_priority", 50)), 50, 1, 100),
            "refresh_minutes": _bounded_int(runtime.get("refresh_minutes", source.get("default_refresh_minutes", 60)), 60, 5, 10080),
            "cache_ttl_minutes": _bounded_int(runtime.get("cache_ttl_minutes", source.get("default_cache_ttl_minutes", 60)), 60, 1, 10080),
        }

    def _runtime_health(self, source: Mapping[str, Any], runtime: Mapping[str, Any], effective: Mapping[str, Any]) -> dict[str, Any]:
        if not effective["enabled"]:
            return {"state": "disabled", "freshness": "disabled", "age_minutes": None, "due": False}
        last_success = _parse_iso(runtime.get("last_success_at"))
        last_attempt = _parse_iso(runtime.get("last_attempt_at"))
        now = self.now_fn()
        age_minutes = None if last_success is None else max(0, int((now - last_success).total_seconds() // 60))
        stale_after = _bounded_int(source.get("stale_after_minutes"), effective["refresh_minutes"] * 3, 5, 525600)
        due = last_attempt is None or (now - last_attempt).total_seconds() >= effective["refresh_minutes"] * 60
        failures = _bounded_int(runtime.get("consecutive_failures", 0), 0, 0, 100000)
        last_status = str(runtime.get("last_status") or "never_run")
        if failures > 0 or last_status in {"unavailable", "error"}:
            state = "degraded"
        elif last_success is None:
            state = "never_run"
        elif age_minutes is not None and age_minutes > stale_after:
            state = "stale"
        else:
            state = "healthy"
        freshness = "unknown" if age_minutes is None else ("stale" if age_minutes > stale_after else "fresh")
        return {"state": state, "freshness": freshness, "age_minutes": age_minutes, "due": due}

    def registry(self, *, public: bool = True) -> dict[str, Any]:
        state = self._state()
        rows: list[dict[str, Any]] = []
        for source in self._registry["sources"]:
            feed_id = str(source["feed_id"])
            runtime = deepcopy(state["sources"].get(feed_id, {}))
            effective = self._effective(source, runtime)
            health = self._runtime_health(source, runtime, effective)
            row = deepcopy(source)
            row["effective"] = effective
            row["health"] = health
            row["runtime"] = {
                "last_attempt_at": runtime.get("last_attempt_at"),
                "last_success_at": runtime.get("last_success_at"),
                "last_status": runtime.get("last_status", "never_run"),
                "last_data_state": runtime.get("last_data_state", "unknown"),
                "last_record_count": int(runtime.get("last_record_count", 0) or 0),
                "last_duration_ms": runtime.get("last_duration_ms"),
                "consecutive_failures": int(runtime.get("consecutive_failures", 0) or 0),
                "requests_today": int(runtime.get("requests_today", 0) or 0),
                "request_day": runtime.get("request_day"),
                "last_test_at": runtime.get("last_test_at"),
                "last_test_status": runtime.get("last_test_status"),
            }
            if not public:
                row["runtime"]["last_error"] = runtime.get("last_error")
                row["runtime"]["last_http_status"] = runtime.get("last_http_status")
            rows.append(row)
        rows.sort(key=lambda item: (item["effective"]["priority"], item["label"]))
        summary = self._summary(rows)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SCHEMA_VERSION,
            "generated_at": _iso(self.now_fn()),
            "source_count": len(rows),
            "summary": summary,
            "sources": rows,
            "boundaries": [
                "Public source operations never expose API keys, authorization headers, or complete upstream payloads.",
                "Health describes retrieval operations, freshness, and configuration; it is not a certification of source accuracy.",
                "Licensing metadata is source-level guidance and must be checked against the specific upstream record when terms vary.",
            ],
        }

    @staticmethod
    def _summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        summary = {"enabled": 0, "healthy": 0, "degraded": 0, "stale": 0, "never_run": 0, "disabled": 0, "due": 0}
        for row in rows:
            health = row.get("health") or {}
            state = str(health.get("state") or "never_run")
            if state in summary:
                summary[state] += 1
            if (row.get("effective") or {}).get("enabled"):
                summary["enabled"] += 1
            if health.get("due"):
                summary["due"] += 1
        return summary

    def source(self, feed_id: str, *, public: bool = True) -> dict[str, Any]:
        feed_id = str(feed_id or "").strip().lower().replace("-", "_")
        payload = self.registry(public=public)
        source = next((row for row in payload["sources"] if row["feed_id"] == feed_id), None)
        if source is None:
            raise KeyError(feed_id)
        return {"ok": True, "version": APP_VERSION, "schema": SCHEMA_VERSION, "generated_at": payload["generated_at"], "source": source}

    def effective_sources(self) -> dict[str, dict[str, Any]]:
        return {row["feed_id"]: row for row in self.registry(public=False)["sources"]}

    def update_source(self, feed_id: str, patch: Mapping[str, Any]) -> dict[str, Any]:
        feed_id = str(feed_id or "").strip().lower().replace("-", "_")
        source = self._source_map().get(feed_id)
        if source is None:
            raise KeyError(feed_id)
        allowed = {"enabled", "priority", "refresh_minutes", "cache_ttl_minutes"}
        with _LOCK:
            state = self._state()
            runtime = state["sources"].setdefault(feed_id, {})
            for key, value in patch.items():
                if key not in allowed:
                    continue
                if key == "enabled":
                    runtime[key] = _bool(value)
                elif key == "priority":
                    runtime[key] = _bounded_int(value, int(source.get("default_priority", 50)), 1, 100)
                elif key == "refresh_minutes":
                    runtime[key] = _bounded_int(value, int(source.get("default_refresh_minutes", 60)), 5, 10080)
                elif key == "cache_ttl_minutes":
                    runtime[key] = _bounded_int(value, int(source.get("default_cache_ttl_minutes", 60)), 1, 10080)
            runtime["configuration_updated_at"] = _iso(self.now_fn())
            self._save_state(state)
        return self.source(feed_id, public=False)

    def record_result(
        self,
        feed_id: str,
        *,
        ok: bool,
        data_state: str = "current",
        record_count: int = 0,
        duration_ms: float | int | None = None,
        error: str = "",
        http_status: int | None = None,
        mode: str = "feed",
    ) -> dict[str, Any]:
        feed_id = str(feed_id or "").strip().lower().replace("-", "_")
        if feed_id not in self._source_map():
            raise KeyError(feed_id)
        now = self.now_fn()
        today = now.date().isoformat()
        data_state = str(data_state or "current")
        if data_state not in _ALLOWED_STATES:
            data_state = "current" if ok else "error"
        with _LOCK:
            state = self._state()
            runtime = state["sources"].setdefault(feed_id, {})
            if runtime.get("request_day") != today:
                runtime["request_day"] = today
                runtime["requests_today"] = 0
            runtime["requests_today"] = int(runtime.get("requests_today", 0) or 0) + 1
            runtime["last_attempt_at"] = _iso(now)
            runtime["last_status"] = data_state if ok else "error"
            runtime["last_data_state"] = data_state
            runtime["last_record_count"] = max(0, int(record_count or 0))
            runtime["last_duration_ms"] = round(float(duration_ms), 2) if duration_ms is not None else None
            runtime["last_http_status"] = int(http_status) if http_status is not None else None
            if ok:
                runtime["last_success_at"] = _iso(now)
                runtime["consecutive_failures"] = 0
                runtime.pop("last_error", None)
            else:
                runtime["consecutive_failures"] = int(runtime.get("consecutive_failures", 0) or 0) + 1
                runtime["last_error"] = str(error or "Source retrieval failed")[:240]
            self._save_state(state)
            receipt = {
                "schema": SCHEMA_VERSION,
                "version": APP_VERSION,
                "feed_id": feed_id,
                "recorded_at": _iso(now),
                "mode": str(mode or "feed")[:40],
                "ok": bool(ok),
                "data_state": data_state,
                "record_count": max(0, int(record_count or 0)),
                "duration_ms": runtime["last_duration_ms"],
                "http_status": runtime["last_http_status"],
                "error_class": str(error or "")[:120] if not ok else "",
            }
            _append_jsonl(self.history_path, receipt)
        return receipt

    def history(self, *, feed_id: str = "", limit: int = 100) -> dict[str, Any]:
        feed_id = str(feed_id or "").strip().lower().replace("-", "_")
        rows = _read_jsonl(self.history_path, limit=max(limit * 3, limit))
        if feed_id:
            if feed_id not in self._source_map():
                raise KeyError(feed_id)
            rows = [row for row in rows if row.get("feed_id") == feed_id]
        rows = rows[-max(1, min(int(limit), 500)):]
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SCHEMA_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(rows),
            "history": rows,
        }

    def manual_test(
        self,
        feed_id: str,
        *,
        live: bool = False,
        test_runner: Callable[[str], Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        feed_id = str(feed_id or "").strip().lower().replace("-", "_")
        source = self._source_map().get(feed_id)
        if source is None:
            raise KeyError(feed_id)
        tested_at = _iso(self.now_fn())
        if not live:
            result = {
                "ok": True,
                "mode": "configuration",
                "feed_id": feed_id,
                "tested_at": tested_at,
                "message": "Registry, operational policy, attribution, and runtime storage are ready. No upstream request was made.",
                "live_request_made": False,
            }
        elif test_runner is None:
            result = {
                "ok": False,
                "mode": "live",
                "feed_id": feed_id,
                "tested_at": tested_at,
                "message": "No live test runner is configured.",
                "live_request_made": False,
            }
        else:
            try:
                payload = dict(test_runner(feed_id))
                signal_count = int(payload.get("count", 0) or 0)
                feed_state = payload.get("feed_state") or {}
                active = set(feed_state.get("active_feeds") or [])
                data_state = "current"
                for candidate in ("events", "weather", "nasa_power", "research", "development"):
                    meta = feed_state.get(candidate)
                    if isinstance(meta, dict) and meta.get("data_state"):
                        data_state = str(meta["data_state"])
                        if signal_count:
                            break
                success = feed_id in active and data_state not in {"unavailable", "error"}
                result = {
                    "ok": success,
                    "mode": "live",
                    "feed_id": feed_id,
                    "tested_at": tested_at,
                    "message": "Live source test completed." if success else "Live source test completed without a usable source response.",
                    "live_request_made": True,
                    "signal_count": signal_count,
                    "data_state": data_state,
                }
                self.record_result(feed_id, ok=success, data_state=data_state, record_count=signal_count, mode="manual_test", error="LiveTestUnavailable" if not success else "")
            except Exception as exc:  # protected admin path; expose class, not raw upstream response
                result = {
                    "ok": False,
                    "mode": "live",
                    "feed_id": feed_id,
                    "tested_at": tested_at,
                    "message": "Live source test failed.",
                    "live_request_made": True,
                    "error_class": exc.__class__.__name__,
                }
                self.record_result(feed_id, ok=False, data_state="error", mode="manual_test", error=exc.__class__.__name__)
        with _LOCK:
            state = self._state()
            runtime = state["sources"].setdefault(feed_id, {})
            runtime["last_test_at"] = tested_at
            runtime["last_test_status"] = "passed" if result["ok"] else "failed"
            self._save_state(state)
        result["source"] = self.source(feed_id, public=False)["source"]
        return result

    def control_center(self) -> dict[str, Any]:
        registry = self.registry(public=False)
        return {
            "ok": True,
            "version": APP_VERSION,
            "schema": SCHEMA_VERSION,
            "generated_at": registry["generated_at"],
            "summary": registry["summary"],
            "sources": registry["sources"],
            "recent_history": self.history(limit=50)["history"],
            "capabilities": {
                "source_enablement": True,
                "source_priority": True,
                "refresh_policy": True,
                "cache_policy": True,
                "rate_tracking": True,
                "failure_history": True,
                "manual_test": True,
                "license_attribution": True,
                "coverage_metadata": True,
                "quality_status": True,
            },
        }
