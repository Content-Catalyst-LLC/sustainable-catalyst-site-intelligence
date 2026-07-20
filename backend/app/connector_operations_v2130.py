from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from .config import Settings

SCHEMA_VERSION = "sc-site-intelligence-connector-operations/1.0"
RELEASE_VERSION = "3.1.4"

_LOCK = threading.RLock()
_SECRET_FRAGMENTS = ("key", "token", "secret", "password", "authorization", "credential", "cookie")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
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

def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return deepcopy(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else deepcopy(default)
    except (OSError, json.JSONDecodeError):
        return deepcopy(default)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _read_jsonl(path: Path, limit: int = 500) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return []
    return rows[-max(1, limit):]


def _safe_preview(value: Any, depth: int = 0) -> Any:
    if depth > 3:
        return "[truncated]"
    if isinstance(value, Mapping):
        preview: Dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 20:
                preview["_truncated"] = True
                break
            label = str(key)
            if any(fragment in label.lower() for fragment in _SECRET_FRAGMENTS):
                preview[label] = "[redacted]"
            else:
                preview[label] = _safe_preview(item, depth + 1)
        return preview
    if isinstance(value, list):
        return [_safe_preview(item, depth + 1) for item in value[:5]] + (["[truncated]"] if len(value) > 5 else [])
    if isinstance(value, str) and len(value) > 240:
        return value[:237] + "..."
    return value


def _record_count(payload: Mapping[str, Any]) -> int:
    for key in ("records", "results", "items", "layers", "latest_rows", "sample_occurrences", "indicators", "sources"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return 1 if payload else 0


class ConnectorOperationsCenter:
    """File-backed, zero-cost connector operations and ingestion control plane.

    The control plane records receipts and sanitized previews. It never persists
    provider credentials, request headers, or complete upstream payloads.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        now_fn: Callable[[], datetime] = _now,
        sleep_fn: Callable[[float], None] = time.sleep,
        adapter_runner: Optional[Callable[[str, Settings, bool], Mapping[str, Any]]] = None,
    ) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.sleep_fn = sleep_fn
        self.adapter_runner = adapter_runner
        self.registry_path = _resolve_path(settings.connector_operations_registry_path)
        self.state_path = _resolve_path(settings.connector_operations_state_path)
        self.history_path = _resolve_path(settings.connector_operations_history_path)
        self.quarantine_path = _resolve_path(settings.connector_operations_quarantine_path)
        self._registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        registry = _read_json(self.registry_path, {})
        if registry.get("schema") != SCHEMA_VERSION:
            raise ValueError(f"Invalid connector operations registry schema at {self.registry_path}")
        if not isinstance(registry.get("connectors"), list) or not isinstance(registry.get("jobs"), list):
            raise ValueError("Connector operations registry must contain connector and job lists.")
        connector_ids = [item.get("connector_id") for item in registry["connectors"]]
        if not all(isinstance(item, str) and item for item in connector_ids) or len(set(connector_ids)) != len(connector_ids):
            raise ValueError("Connector IDs must be unique non-empty strings.")
        known = set(connector_ids)
        job_ids: set[str] = set()
        for job in registry["jobs"]:
            job_id = str(job.get("job_id") or "")
            if not job_id or job_id in job_ids or job.get("connector_id") not in known:
                raise ValueError("Jobs must have unique IDs and reference registered connectors.")
            job_ids.add(job_id)
        return registry

    def _default_state(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "updated_at": _iso(self.now_fn()),
            "connectors": {},
            "rate_windows": {},
            "datasets": {},
            "quarantine_resolutions": {},
        }

    def _state(self) -> Dict[str, Any]:
        state = _read_json(self.state_path, self._default_state())
        state.setdefault("connectors", {})
        state.setdefault("rate_windows", {})
        state.setdefault("datasets", {})
        state.setdefault("quarantine_resolutions", {})
        return state

    def _save_state(self, state: Dict[str, Any]) -> None:
        state["schema"] = SCHEMA_VERSION
        state["version"] = RELEASE_VERSION
        state["updated_at"] = _iso(self.now_fn())
        _atomic_write_json(self.state_path, state)

    def _connector_map(self) -> Dict[str, Dict[str, Any]]:
        return {item["connector_id"]: item for item in self._registry["connectors"]}

    def _job_map(self) -> Dict[str, Dict[str, Any]]:
        return {item["job_id"]: item for item in self._registry["jobs"]}

    def registry(self, public: bool = False) -> Dict[str, Any]:
        state = self._state()
        connectors = []
        for raw in self._registry["connectors"]:
            item = deepcopy(raw)
            runtime = deepcopy(state["connectors"].get(item["connector_id"], {}))
            credentials = item.pop("credential_env_names", [])
            item["credentials_required"] = item.get("credential_strategy") not in {"none", ""}
            item["credentials_configured"] = self._credentials_configured(credentials)
            if public:
                item.pop("adapter", None)
                item.pop("quota", None)
                item.pop("schema_contract", None)
                item.pop("transformations", None)
                item["credentials_configured"] = None
                runtime.pop("last_error", None)
                runtime.pop("circuit_open_until", None)
            item["runtime"] = runtime
            connectors.append(item)
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "connector_count": len(connectors),
            "connectors": connectors,
        }

    def jobs(self) -> Dict[str, Any]:
        connectors = self._connector_map()
        state = self._state()
        rows = []
        for raw in self._registry["jobs"]:
            item = deepcopy(raw)
            connector = connectors[item["connector_id"]]
            runtime = state["connectors"].get(item["connector_id"], {})
            item["schedule"] = deepcopy(connector.get("schedule", {}))
            item["expected_update"] = deepcopy(connector.get("expected_update", {}))
            item["last_execution_at"] = runtime.get("last_execution_at")
            item["last_success_at"] = runtime.get("last_success_at")
            item["last_status"] = runtime.get("last_status", "never_run")
            rows.append(item)
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "job_count": len(rows),
            "jobs": rows,
        }

    def due_jobs(self) -> Dict[str, Any]:
        now = self.now_fn()
        connectors = self._connector_map()
        state = self._state()
        due: List[Dict[str, Any]] = []
        for job in self._registry["jobs"]:
            if not job.get("enabled", True):
                continue
            connector = connectors[job["connector_id"]]
            runtime = state["connectors"].get(job["connector_id"], {})
            last_execution = _parse_iso(runtime.get("last_execution_at"))
            interval = int(connector.get("schedule", {}).get("interval_minutes", 1440))
            schedule_due = last_execution is None or now >= last_execution + timedelta(minutes=interval)
            max_age = int(connector.get("expected_update", {}).get("max_age_hours", 48))
            last_success = _parse_iso(runtime.get("last_success_at"))
            stale = last_success is None or now >= last_success + timedelta(hours=max_age)
            failed = int(runtime.get("consecutive_failures", 0)) > 0
            reasons = []
            if schedule_due and "scheduled" in job.get("triggers", []):
                reasons.append("schedule_due")
            if (stale or failed) and "conditional" in job.get("triggers", []):
                reasons.append("stale_or_failed")
            if reasons:
                due.append({
                    "job_id": job["job_id"],
                    "connector_id": job["connector_id"],
                    "name": job["name"],
                    "reasons": reasons,
                    "last_execution_at": runtime.get("last_execution_at"),
                    "last_success_at": runtime.get("last_success_at"),
                })
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "generated_at": _iso(now),
            "due_count": len(due),
            "due_jobs": due,
        }

    def run_due_jobs(
        self,
        *,
        dry_run: bool = True,
        force: bool = False,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """Execute jobs currently due by schedule or stale/failed condition.

        The control center does not imply that a background scheduler exists. This
        method is the explicit runner used by the protected API, CLI, or an
        external scheduler. Dry-run is the safe default.
        """
        limit = max(1, min(int(limit), 100))
        due = self.due_jobs()["due_jobs"][:limit]
        executions: List[Dict[str, Any]] = []
        for item in due:
            reasons = item.get("reasons", [])
            trigger = "conditional" if "stale_or_failed" in reasons else "scheduled"
            executions.append(
                self.run_job(
                    item["job_id"],
                    trigger=trigger,
                    dry_run=dry_run,
                    force=force,
                )
            )
        counts: Dict[str, int] = {}
        for receipt in executions:
            status = str(receipt.get("status") or "unknown")
            counts[status] = counts.get(status, 0) + 1
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "dry_run": bool(dry_run),
            "requested_limit": limit,
            "due_count": len(due),
            "executed_count": len(executions),
            "status_counts": counts,
            "executions": executions,
            "scheduler_boundary": "This batch was invoked explicitly; the response does not imply a persistent background scheduler is configured.",
        }

    def executions(self, *, limit: int = 100, connector_id: str = "", status: str = "") -> Dict[str, Any]:
        limit = max(1, min(int(limit), self.settings.connector_operations_max_history))
        rows = _read_jsonl(self.history_path, self.settings.connector_operations_max_history)
        if connector_id:
            rows = [row for row in rows if row.get("connector_id") == connector_id]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        rows = list(reversed(rows[-limit:]))
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(rows),
            "executions": rows,
        }

    def quarantine(self, *, limit: int = 100, status: str = "open") -> Dict[str, Any]:
        state = self._state()
        resolutions = state.get("quarantine_resolutions", {})
        rows = _read_jsonl(self.quarantine_path, self.settings.connector_operations_max_history)
        result = []
        for row in reversed(rows[-max(1, min(limit, self.settings.connector_operations_max_history)):]):
            resolution = resolutions.get(row.get("quarantine_id"), {})
            item = {**row, "resolution": resolution or None, "resolution_status": resolution.get("action", "open") if resolution else "open"}
            if status and item["resolution_status"] != status:
                continue
            result.append(item)
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(result),
            "items": result,
        }

    def resolve_quarantine(self, quarantine_id: str, action: str, note: str = "") -> Dict[str, Any]:
        if action not in {"accept", "reject", "retry"}:
            raise ValueError("Quarantine action must be accept, reject, or retry.")
        known = {item.get("quarantine_id") for item in _read_jsonl(self.quarantine_path, self.settings.connector_operations_max_history)}
        if quarantine_id not in known:
            raise KeyError(quarantine_id)
        with _LOCK:
            state = self._state()
            resolution = {
                "action": action,
                "note": str(note or "")[:500],
                "resolved_at": _iso(self.now_fn()),
            }
            state["quarantine_resolutions"][quarantine_id] = resolution
            self._save_state(state)
        return {"ok": True, "quarantine_id": quarantine_id, "resolution": resolution}

    def datasets(self) -> Dict[str, Any]:
        state = self._state()
        connector_map = self._connector_map()
        rows = []
        for connector_id, connector in connector_map.items():
            runtime = state["connectors"].get(connector_id, {})
            for dataset_id in connector.get("datasets", []):
                dataset = deepcopy(state["datasets"].get(dataset_id, {}))
                rows.append({
                    "dataset_id": dataset_id,
                    "connector_id": connector_id,
                    "connector_name": connector["name"],
                    "schema_version": connector.get("schema_contract", {}).get("schema_version", "1.0"),
                    "expected_update": connector.get("expected_update", {}),
                    "last_accepted_at": dataset.get("last_accepted_at"),
                    "last_record_count": dataset.get("last_record_count", 0),
                    "last_payload_digest": dataset.get("last_payload_digest"),
                    "last_status": runtime.get("last_status", "never_run"),
                    "freshness_state": self._freshness_state(connector, runtime),
                })
        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "dataset_count": len(rows),
            "datasets": rows,
        }

    def control_center(self) -> Dict[str, Any]:
        registry = self.registry(public=False)
        jobs = self.jobs()
        due = self.due_jobs()
        datasets = self.datasets()
        executions = self.executions(limit=20)
        quarantine = self.quarantine(limit=20, status="open")
        connectors = registry["connectors"]
        counts: Dict[str, int] = {"healthy": 0, "stale": 0, "degraded": 0, "never_run": 0, "circuit_open": 0}
        for connector in connectors:
            state = connector.get("runtime", {})
            status = self._operational_status(connector, state)
            counts[status] = counts.get(status, 0) + 1
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "title": "Connector Operations and Data Ingestion Control Center",
            "summary": "Managed connector registry, refresh jobs, execution receipts, freshness, quotas, circuit breakers, schema validation, quarantine, and dataset diagnostics.",
            "enabled": self.settings.connector_operations_enabled,
            "counts": {
                "connectors": registry["connector_count"],
                "jobs": jobs["job_count"],
                "due_jobs": due["due_count"],
                "datasets": datasets["dataset_count"],
                "recent_executions": executions["count"],
                "open_quarantine": quarantine["count"],
                **counts,
            },
            "paths": {
                "registry": str(self.registry_path),
                "state": str(self.state_path),
                "history": str(self.history_path),
                "quarantine": str(self.quarantine_path),
            },
            "connectors": connectors,
            "due_jobs": due["due_jobs"],
            "datasets": datasets["datasets"],
            "recent_executions": executions["executions"],
            "open_quarantine": quarantine["items"],
            "governance": [
                "Credential values, request headers, and complete upstream payloads are never returned or persisted by this control center.",
                "Execution receipts prove what the ingestion pipeline did; they do not certify upstream factual accuracy or completeness.",
                "Scheduled and conditional jobs are evaluated by the backend but require an explicit runner or external scheduler to invoke due jobs.",
                "Public status exposes sanitized operational summaries only.",
            ],
        }

    def public_status(self) -> Dict[str, Any]:
        registry = self.registry(public=True)
        state = self._state()
        rows = []
        counts: Dict[str, int] = {"healthy": 0, "stale": 0, "degraded": 0, "never_run": 0, "circuit_open": 0}
        for connector in registry["connectors"]:
            runtime = state["connectors"].get(connector["connector_id"], {})
            operational = self._operational_status(connector, runtime)
            counts[operational] = counts.get(operational, 0) + 1
            rows.append({
                "connector_id": connector["connector_id"],
                "name": connector["name"],
                "provider": connector["provider"],
                "family": connector["family"],
                "public_status": connector["public_status"],
                "operational_status": operational,
                "freshness_state": self._freshness_state(connector, runtime),
                "last_success_at": runtime.get("last_success_at"),
                "last_status": runtime.get("last_status", "never_run"),
                "public_note": connector.get("public_note", ""),
            })
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "title": "Public Connector Operations Status",
            "summary": "Sanitized connector availability and freshness summary. No credentials, quotas, raw payloads, or private execution details are exposed.",
            "counts": counts,
            "connectors": rows,
            "recommended_shortcode": "[sc_public_connector_operations]",
            "boundaries": [
                "Operational status is not a guarantee of real-time completeness or factual accuracy.",
                "A cached or fallback-safe connector can remain publicly usable while live retrieval is unavailable.",
                "Private diagnostics, provider limits, credentials, and quarantined payload previews remain hidden.",
            ],
        }

    def run_job(
        self,
        job_id: str,
        *,
        trigger: str = "manual",
        dry_run: bool = True,
        supplied_payload: Optional[Mapping[str, Any]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        jobs = self._job_map()
        connectors = self._connector_map()
        if job_id not in jobs:
            raise KeyError(job_id)
        job = jobs[job_id]
        connector = connectors[job["connector_id"]]
        if trigger not in job.get("triggers", ["manual"]):
            raise ValueError(f"Trigger {trigger!r} is not allowed for {job_id}.")
        if not job.get("enabled", True) or not connector.get("enabled", True):
            return self._blocked_receipt(job, connector, trigger, "disabled")

        with _LOCK:
            state = self._state()
            runtime = state["connectors"].setdefault(connector["connector_id"], {})
            blocked = self._circuit_block(runtime, force=force)
            if blocked:
                receipt = self._blocked_receipt(job, connector, trigger, "circuit_open", blocked)
                self._record_execution(receipt)
                return receipt
            if not dry_run and not self._consume_quota(state, connector, force=force):
                receipt = self._blocked_receipt(job, connector, trigger, "quota_exceeded")
                self._record_execution(receipt)
                self._save_state(state)
                return receipt
            self._save_state(state)

        execution_id = f"exec-{uuid4().hex[:16]}"
        started = self.now_fn()
        attempts = 0
        max_attempts = 1 if dry_run else self.settings.connector_operations_default_retry_attempts
        last_error = ""
        payload: Mapping[str, Any] = {}
        while attempts < max_attempts:
            attempts += 1
            try:
                if dry_run:
                    payload = self._dry_run_payload(connector)
                elif supplied_payload is not None:
                    payload = dict(supplied_payload)
                else:
                    payload = dict(self._run_adapter(connector["adapter"], force_refresh=force))
                if not isinstance(payload, Mapping):
                    raise TypeError("Connector adapter returned a non-object payload.")
                break
            except Exception as exc:  # Connector failures must become receipts, not server crashes.
                last_error = f"{type(exc).__name__}: {exc}"[:500]
                if attempts < max_attempts:
                    delay = self.settings.connector_operations_retry_backoff_seconds * (2 ** (attempts - 1))
                    if delay > 0:
                        self.sleep_fn(delay)
        else:
            payload = {}

        validation = self._validate_payload(connector, payload)
        finished = self.now_fn()
        receipt: Dict[str, Any] = {
            "execution_id": execution_id,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "job_id": job_id,
            "connector_id": connector["connector_id"],
            "connector_name": connector["name"],
            "operation": job.get("operation", "refresh"),
            "trigger": trigger,
            "dry_run": bool(dry_run),
            "started_at": _iso(started),
            "finished_at": _iso(finished),
            "duration_ms": max(0, int((finished - started).total_seconds() * 1000)),
            "attempts": attempts,
            "record_count": _record_count(payload),
            "payload_digest": _digest(payload) if payload else None,
            "schema_version": connector.get("schema_contract", {}).get("schema_version", "1.0"),
            "transformations": connector.get("transformations", []),
            "validation": validation,
            "source_state": self._source_state(payload),
            "status": "accepted" if validation["valid"] else "quarantined",
            "error": last_error or None,
        }

        if last_error and not payload:
            receipt["status"] = "failed"
            receipt["validation"] = {"valid": False, "errors": [last_error], "required_fields": validation["required_fields"]}
        elif not validation["valid"]:
            quarantine_id = f"quarantine-{uuid4().hex[:16]}"
            receipt["quarantine_id"] = quarantine_id
            self._record_quarantine(quarantine_id, receipt, payload)

        if (
            receipt["status"] == "accepted"
            and not dry_run
            and self.settings.historical_archive_enabled
            and self.settings.historical_archive_capture_on_ingest
        ):
            try:
                from .historical_archive_v2140 import HistoricalArchiveCenter
                receipt["historical_archive"] = HistoricalArchiveCenter(self.settings).capture_ingestion(connector, receipt, payload)
            except Exception as exc:  # Archival failure must not falsify ingestion acceptance.
                receipt["historical_archive"] = {
                    "ok": False,
                    "version": "3.1.4",
                    "error": f"{type(exc).__name__}: {exc}"[:500],
                    "ingestion_status_unchanged": True,
                }

        with _LOCK:
            state = self._state()
            runtime = state["connectors"].setdefault(connector["connector_id"], {})
            runtime["last_execution_at"] = receipt["finished_at"]
            runtime["last_status"] = receipt["status"]
            runtime["last_record_count"] = receipt["record_count"]
            runtime["last_payload_digest"] = receipt["payload_digest"]
            runtime["last_source_state"] = receipt["source_state"]
            runtime["execution_count"] = int(runtime.get("execution_count", 0)) + 1
            if receipt["status"] == "accepted":
                runtime["last_success_at"] = receipt["finished_at"]
                runtime["consecutive_failures"] = 0
                runtime["last_error"] = None
                runtime["circuit_open_until"] = None
                for dataset_id in connector.get("datasets", []):
                    state["datasets"][dataset_id] = {
                        "connector_id": connector["connector_id"],
                        "last_accepted_at": receipt["finished_at"],
                        "last_record_count": receipt["record_count"],
                        "last_payload_digest": receipt["payload_digest"],
                        "schema_version": receipt["schema_version"],
                    }
            else:
                runtime["last_failure_at"] = receipt["finished_at"]
                runtime["last_error"] = receipt.get("error") or "; ".join(receipt["validation"].get("errors", []))[:500]
                runtime["consecutive_failures"] = int(runtime.get("consecutive_failures", 0)) + 1
                if runtime["consecutive_failures"] >= self.settings.connector_operations_circuit_breaker_failures:
                    runtime["circuit_open_until"] = _iso(self.now_fn() + timedelta(seconds=self.settings.connector_operations_circuit_breaker_seconds))
            self._save_state(state)
            self._record_execution(receipt)
        return receipt

    def _run_adapter(self, adapter: str, force_refresh: bool) -> Mapping[str, Any]:
        if self.adapter_runner is not None:
            return self.adapter_runner(adapter, self.settings, force_refresh)
        if adapter.startswith("external."):
            from .connectors.external_data import ExternalDataHub
            hub = ExternalDataHub(self.settings)
            name = adapter.split(".", 1)[1]
            if name == "nasa_power":
                return hub.nasa_power_timeseries(force_refresh=force_refresh)
            if name == "nasa_gibs":
                return hub.nasa_gibs_layers(force_refresh=force_refresh)
            if name == "climate_trace":
                return hub.climate_trace_emissions(force_refresh=force_refresh)
        if adapter.startswith("advanced."):
            from .connectors.advanced_external import AdvancedExternalDataHub
            hub = AdvancedExternalDataHub(self.settings)
            name = adapter.split(".", 1)[1]
            method = getattr(hub, name)
            return method(force_refresh=force_refresh)
        if adapter.startswith("public."):
            name = adapter.split(".", 1)[1]
            if name in {"world_bank", "openalex", "crossref", "github"}:
                from .public_live_connectors import public_connector_detail
                return public_connector_detail(name.replace("_", "-"), self.settings)
            if name == "sustainable_development":
                from .sustainable_development_connectors import source_registry
                return source_registry(self.settings)
        raise KeyError(f"No adapter registered for {adapter}")

    def _dry_run_payload(self, connector: Mapping[str, Any]) -> Dict[str, Any]:
        required = connector.get("schema_contract", {}).get("required_fields", [])
        payload: Dict[str, Any] = {
            "source": connector.get("provider"),
            "ok": True,
            "connector": {"connector_id": connector.get("connector_id"), "name": connector.get("name")},
            "indicators": [],
            "layers": [],
            "sources": [],
            "dry_run": True,
        }
        return {key: payload.get(key) for key in set(required) | {"dry_run"}}

    def _validate_payload(self, connector: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        required = [str(item) for item in connector.get("schema_contract", {}).get("required_fields", [])]
        errors = []
        for field in required:
            if field not in payload or payload.get(field) is None:
                errors.append(f"Missing required field: {field}")
        if len(_canonical_bytes(payload)) > self.settings.connector_operations_max_payload_bytes:
            errors.append("Payload exceeds configured ingestion size limit.")
        records = _record_count(payload)
        if records > self.settings.connector_operations_max_records_per_run:
            errors.append("Record count exceeds configured per-run limit.")
        return {"valid": not errors, "errors": errors, "required_fields": required}

    def _record_quarantine(self, quarantine_id: str, receipt: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
        item = {
            "quarantine_id": quarantine_id,
            "created_at": receipt["finished_at"],
            "execution_id": receipt["execution_id"],
            "job_id": receipt["job_id"],
            "connector_id": receipt["connector_id"],
            "payload_digest": receipt.get("payload_digest"),
            "record_count": receipt.get("record_count", 0),
            "validation_errors": receipt.get("validation", {}).get("errors", []),
            "payload_preview": _safe_preview(payload),
            "raw_payload_persisted": False,
        }
        _append_jsonl(self.quarantine_path, item)

    def _record_execution(self, receipt: Mapping[str, Any]) -> None:
        safe = dict(receipt)
        safe.pop("payload", None)
        _append_jsonl(self.history_path, safe)

    def _blocked_receipt(
        self,
        job: Mapping[str, Any],
        connector: Mapping[str, Any],
        trigger: str,
        reason: str,
        blocked_until: str | None = None,
    ) -> Dict[str, Any]:
        now = _iso(self.now_fn())
        return {
            "execution_id": f"exec-{uuid4().hex[:16]}",
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "job_id": job["job_id"],
            "connector_id": connector["connector_id"],
            "connector_name": connector["name"],
            "operation": job.get("operation", "refresh"),
            "trigger": trigger,
            "dry_run": False,
            "started_at": now,
            "finished_at": now,
            "duration_ms": 0,
            "attempts": 0,
            "record_count": 0,
            "payload_digest": None,
            "validation": {"valid": False, "errors": [reason], "required_fields": []},
            "source_state": "not_requested",
            "status": "blocked",
            "blocked_reason": reason,
            "blocked_until": blocked_until,
            "error": None,
        }

    def _circuit_block(self, runtime: Mapping[str, Any], *, force: bool) -> Optional[str]:
        if force:
            return None
        until = _parse_iso(runtime.get("circuit_open_until"))
        if until and self.now_fn() < until:
            return _iso(until)
        return None

    def _consume_quota(self, state: Dict[str, Any], connector: Mapping[str, Any], *, force: bool) -> bool:
        if force:
            return True
        now = self.now_fn()
        quota = connector.get("quota", {})
        minute_limit = int(quota.get("requests_per_minute", 60))
        day_limit = int(quota.get("requests_per_day", 10000))
        window = state["rate_windows"].setdefault(connector["connector_id"], {})
        minute_key = now.strftime("%Y-%m-%dT%H:%M")
        day_key = now.strftime("%Y-%m-%d")
        if window.get("minute_key") != minute_key:
            window["minute_key"] = minute_key
            window["minute_count"] = 0
        if window.get("day_key") != day_key:
            window["day_key"] = day_key
            window["day_count"] = 0
        if int(window.get("minute_count", 0)) >= minute_limit or int(window.get("day_count", 0)) >= day_limit:
            return False
        window["minute_count"] = int(window.get("minute_count", 0)) + 1
        window["day_count"] = int(window.get("day_count", 0)) + 1
        return True

    def _credentials_configured(self, names: Iterable[str]) -> bool:
        names = list(names)
        if not names:
            return True
        for name in names:
            field = name.removeprefix("SC_SI_").lower()
            if not str(getattr(self.settings, field, "") or "").strip():
                return False
        return True

    def _source_state(self, payload: Mapping[str, Any]) -> str:
        if payload.get("dry_run"):
            return "dry_run"
        cache = payload.get("cache")
        if isinstance(cache, Mapping) and cache.get("status"):
            return str(cache.get("status"))
        if payload.get("live") is True:
            return "live"
        if payload.get("ok") is True:
            return "metadata_ready"
        return "unknown"

    def _freshness_state(self, connector: Mapping[str, Any], runtime: Mapping[str, Any]) -> str:
        last_success = _parse_iso(runtime.get("last_success_at"))
        if last_success is None:
            return "never_ingested"
        max_age = int(connector.get("expected_update", {}).get("max_age_hours", 48))
        return "fresh" if self.now_fn() < last_success + timedelta(hours=max_age) else "stale"

    def _operational_status(self, connector: Mapping[str, Any], runtime: Mapping[str, Any]) -> str:
        until = _parse_iso(runtime.get("circuit_open_until"))
        if until and self.now_fn() < until:
            return "circuit_open"
        if not runtime.get("last_execution_at"):
            return "never_run"
        if runtime.get("last_status") in {"failed", "quarantined", "blocked"}:
            return "degraded"
        if self._freshness_state(connector, runtime) == "stale":
            return "stale"
        return "healthy"
