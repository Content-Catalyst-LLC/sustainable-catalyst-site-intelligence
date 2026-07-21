from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from .config import Settings

SCHEMA_VERSION = "sc-site-intelligence-historical-archive/1.0"
SNAPSHOT_SCHEMA = "sc-site-intelligence-dataset-snapshot/1.0"
CHANGE_SCHEMA = "sc-site-intelligence-temporal-change/1.0"
REVISION_SCHEMA = "sc-site-intelligence-source-revision/1.0"
RELEASE_VERSION = "3.10.0"

_LOCK = threading.RLock()
_SECRET_FRAGMENTS = (
    "key",
    "token",
    "secret",
    "password",
    "authorization",
    "credential",
    "cookie",
    "session",
)
_DEFAULT_POLICY = {
    "schema": SCHEMA_VERSION,
    "version": RELEASE_VERSION,
    "timestamp_fields": ["source_timestamp", "updated_at", "last_updated", "retrieved_at", "generated_at", "timestamp", "date"],
    "revision_fields": ["source_revision_id", "revision", "dataset_version", "release", "version"],
    "comparison_ignored_paths": [
        "retrieved_at",
        "generated_at",
        "ingested_at",
        "ingestion_timestamp",
        "request_id",
        "execution_id",
    ],
    "public_payload_access": False,
    "minimum_snapshots_to_keep": 2,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso(value: Any) -> Optional[datetime]:
    if value is None or value == "":
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


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return deepcopy(default)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else deepcopy(default)
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


def _read_jsonl(path: Path, limit: int = 10000) -> List[Dict[str, Any]]:
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


def _rewrite_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, default=str) + "\n")
    os.replace(temporary, path)


def _sanitize(value: Any, depth: int = 0) -> Any:
    if depth > 12:
        return "[truncated]"
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            label = str(key)
            if any(fragment in label.lower() for fragment in _SECRET_FRAGMENTS):
                result[label] = "[redacted]"
            else:
                result[label] = _sanitize(item, depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, depth + 1) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _record_count(payload: Mapping[str, Any]) -> int:
    for key in ("records", "results", "items", "layers", "latest_rows", "sample_occurrences", "indicators", "sources", "observations"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return 1 if payload else 0


def _flatten(value: Any, prefix: str = "", *, max_items: int = 2000) -> Dict[str, Any]:
    output: Dict[str, Any] = {}

    def visit(item: Any, path: str) -> None:
        if len(output) >= max_items:
            return
        if isinstance(item, Mapping):
            for key in sorted(item, key=lambda candidate: str(candidate)):
                child = f"{path}.{key}" if path else str(key)
                visit(item[key], child)
            return
        if isinstance(item, list):
            for index, child_item in enumerate(item[:250]):
                child = f"{path}[{index}]" if path else f"[{index}]"
                visit(child_item, child)
            if len(item) > 250:
                output[f"{path}.__truncated_count"] = len(item) - 250
            return
        output[path or "value"] = item

    visit(value, prefix)
    return output


def _get_path(value: Any, path: str) -> Any:
    if not path:
        return None
    current = value
    for part in path.split("."):
        if "[" in part and part.endswith("]"):
            label, raw_index = part[:-1].split("[", 1)
            if label:
                if not isinstance(current, Mapping):
                    return None
                current = current.get(label)
            if not isinstance(current, list):
                return None
            try:
                current = current[int(raw_index)]
            except (ValueError, IndexError):
                return None
        else:
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
    return current


class HistoricalArchiveCenter:
    """File-backed historical snapshots, temporal changes, and source revisions.

    Snapshot payloads are sanitized before persistence. Public methods return
    metadata and derived series only; archived payload bodies remain private.
    """

    def __init__(self, settings: Settings, *, now_fn=_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.root_path = _resolve_path(settings.historical_archive_root_path)
        self.snapshot_root = self.root_path / "snapshots"
        self.index_path = _resolve_path(settings.historical_archive_index_path)
        self.change_path = _resolve_path(settings.historical_archive_change_path)
        self.revision_path = _resolve_path(settings.historical_archive_revision_path)
        self.retention_log_path = _resolve_path(settings.historical_archive_retention_log_path)
        self.policy_path = _resolve_path(settings.historical_archive_policy_path)
        self.policy = _read_json(self.policy_path, _DEFAULT_POLICY)
        if self.policy.get("schema") != SCHEMA_VERSION:
            raise ValueError(f"Invalid historical archive policy schema at {self.policy_path}")

    def _snapshot_rows(self) -> List[Dict[str, Any]]:
        return _read_jsonl(self.index_path, self.settings.historical_archive_max_index_records)

    def _change_rows(self) -> List[Dict[str, Any]]:
        return _read_jsonl(self.change_path, self.settings.historical_archive_max_index_records)

    def _revision_rows(self) -> List[Dict[str, Any]]:
        return _read_jsonl(self.revision_path, self.settings.historical_archive_max_index_records)

    def _snapshot_path(self, dataset_id: str, snapshot_id: str, captured_at: datetime) -> Path:
        stamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
        safe_dataset = "".join(character if character.isalnum() or character in "-_" else "-" for character in dataset_id)
        return self.snapshot_root / safe_dataset / f"{stamp}-{snapshot_id}.json"

    def _load_envelope(self, metadata: Mapping[str, Any]) -> Dict[str, Any]:
        relative = str(metadata.get("storage_path") or "")
        if not relative:
            raise FileNotFoundError("Snapshot storage path is unavailable.")
        path = self.root_path / relative
        envelope = _read_json(path, {})
        if envelope.get("schema") != SNAPSHOT_SCHEMA:
            raise ValueError(f"Invalid snapshot envelope: {metadata.get('snapshot_id')}")
        payload = envelope.get("payload")
        if _digest(payload) != envelope.get("payload_digest"):
            raise ValueError(f"Snapshot digest verification failed: {metadata.get('snapshot_id')}")
        return envelope

    def _latest(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        rows = [row for row in self._snapshot_rows() if row.get("dataset_id") == dataset_id]
        return rows[-1] if rows else None

    def _extract_field(self, payload: Mapping[str, Any], fields: Iterable[str]) -> Optional[str]:
        for field in fields:
            value = _get_path(payload, str(field))
            if value not in (None, ""):
                return str(value)
        return None

    def _compare(self, previous: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, Any]:
        ignored = {str(item) for item in self.policy.get("comparison_ignored_paths", [])}
        before = {key: value for key, value in _flatten(previous).items() if key not in ignored and key.split(".")[-1] not in ignored}
        after = {key: value for key, value in _flatten(current).items() if key not in ignored and key.split(".")[-1] not in ignored}
        keys = sorted(set(before) | set(after))
        added: List[str] = []
        removed: List[str] = []
        changed: List[str] = []
        numeric_changes: List[Dict[str, Any]] = []
        for key in keys:
            if key not in before:
                added.append(key)
                continue
            if key not in after:
                removed.append(key)
                continue
            if before[key] == after[key]:
                continue
            changed.append(key)
            left = before[key]
            right = after[key]
            if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
                delta = right - left
                percent = None if left == 0 else (delta / abs(left)) * 100
                numeric_changes.append({
                    "path": key,
                    "previous": left,
                    "current": right,
                    "delta": delta,
                    "percent_change": percent,
                })
        changed_count = len(added) + len(removed) + len(changed)
        field_count = max(1, len(keys))
        return {
            "changed": changed_count > 0,
            "field_count": field_count,
            "changed_field_count": changed_count,
            "change_ratio": changed_count / field_count,
            "added_paths": added[:100],
            "removed_paths": removed[:100],
            "changed_paths": changed[:150],
            "numeric_changes": numeric_changes[:100],
            "details_truncated": len(added) > 100 or len(removed) > 100 or len(changed) > 150 or len(numeric_changes) > 100,
        }

    def capture_ingestion(
        self,
        connector: Mapping[str, Any],
        receipt: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        results = []
        for dataset_id in connector.get("datasets", []):
            results.append(
                self.capture_snapshot(
                    dataset_id=str(dataset_id),
                    connector_id=str(connector.get("connector_id") or ""),
                    payload=payload,
                    execution_id=str(receipt.get("execution_id") or ""),
                    schema_version=str(receipt.get("schema_version") or "1.0"),
                )
            )
        return {
            "ok": all(item.get("ok", False) for item in results),
            "version": RELEASE_VERSION,
            "snapshot_results": results,
        }

    def capture_snapshot(
        self,
        *,
        dataset_id: str,
        connector_id: str,
        payload: Mapping[str, Any],
        execution_id: str = "",
        schema_version: str = "1.0",
        source_timestamp: str = "",
        source_revision_id: str = "",
        note: str = "",
        force: bool = False,
    ) -> Dict[str, Any]:
        dataset_id = str(dataset_id or "").strip()
        connector_id = str(connector_id or "").strip()
        if not dataset_id or not connector_id:
            raise ValueError("dataset_id and connector_id are required.")
        if not isinstance(payload, Mapping):
            raise ValueError("Snapshot payload must be a JSON object.")
        sanitized = _sanitize(payload)
        encoded = _canonical_bytes(sanitized)
        if len(encoded) > self.settings.historical_archive_max_snapshot_bytes:
            raise ValueError("Snapshot payload exceeds the configured archive size limit.")
        payload_digest = hashlib.sha256(encoded).hexdigest()
        captured = self.now_fn()
        source_timestamp = source_timestamp or self._extract_field(sanitized, self.policy.get("timestamp_fields", [])) or ""
        source_revision_id = source_revision_id or self._extract_field(sanitized, self.policy.get("revision_fields", [])) or ""

        with _LOCK:
            previous = self._latest(dataset_id)
            if previous and previous.get("payload_digest") == payload_digest and not force:
                return {
                    "ok": True,
                    "version": RELEASE_VERSION,
                    "dataset_id": dataset_id,
                    "status": "unchanged",
                    "snapshot_created": False,
                    "snapshot_id": previous.get("snapshot_id"),
                    "payload_digest": payload_digest,
                    "deduplicated": True,
                }

            snapshot_id = f"snapshot-{uuid4().hex[:18]}"
            path = self._snapshot_path(dataset_id, snapshot_id, captured)
            path.parent.mkdir(parents=True, exist_ok=True)
            comparison: Dict[str, Any] = {
                "changed": False,
                "field_count": len(_flatten(sanitized)),
                "changed_field_count": 0,
                "change_ratio": 0.0,
                "added_paths": [],
                "removed_paths": [],
                "changed_paths": [],
                "numeric_changes": [],
                "details_truncated": False,
            }
            previous_payload: Mapping[str, Any] = {}
            if previous:
                previous_payload = self._load_envelope(previous).get("payload", {})
                comparison = self._compare(previous_payload, sanitized)

            same_period_revision = bool(
                previous
                and comparison["changed"]
                and source_timestamp
                and source_timestamp == str(previous.get("source_timestamp") or "")
            )
            explicit_revision = bool(
                previous
                and comparison["changed"]
                and source_revision_id
                and source_revision_id != str(previous.get("source_revision_id") or "")
            )
            change_type = "initial_snapshot"
            if previous:
                change_type = "source_revision" if same_period_revision or explicit_revision else "data_update"
            material = bool(
                comparison["changed"]
                and comparison["change_ratio"] >= self.settings.historical_archive_material_change_ratio
            ) or same_period_revision or explicit_revision

            envelope = {
                "schema": SNAPSHOT_SCHEMA,
                "version": RELEASE_VERSION,
                "snapshot_id": snapshot_id,
                "dataset_id": dataset_id,
                "connector_id": connector_id,
                "captured_at": _iso(captured),
                "source_timestamp": source_timestamp or None,
                "source_revision_id": source_revision_id or None,
                "schema_version": schema_version,
                "payload_digest": payload_digest,
                "payload": sanitized,
            }
            _atomic_write_json(path, envelope)
            relative_path = str(path.relative_to(self.root_path))
            metadata = {
                "schema": SNAPSHOT_SCHEMA,
                "version": RELEASE_VERSION,
                "snapshot_id": snapshot_id,
                "dataset_id": dataset_id,
                "connector_id": connector_id,
                "captured_at": _iso(captured),
                "source_timestamp": source_timestamp or None,
                "source_revision_id": source_revision_id or None,
                "execution_id": execution_id or None,
                "schema_version": schema_version,
                "record_count": _record_count(sanitized),
                "payload_bytes": len(encoded),
                "payload_digest": payload_digest,
                "previous_snapshot_id": previous.get("snapshot_id") if previous else None,
                "change_type": change_type,
                "material_change": material,
                "change_ratio": comparison["change_ratio"],
                "changed_field_count": comparison["changed_field_count"],
                "storage_path": relative_path,
                "note": str(note or "")[:500] or None,
            }
            _append_jsonl(self.index_path, metadata)

            change_event = None
            revision_event = None
            if previous and comparison["changed"]:
                change_event = {
                    "schema": CHANGE_SCHEMA,
                    "version": RELEASE_VERSION,
                    "change_id": f"change-{uuid4().hex[:18]}",
                    "dataset_id": dataset_id,
                    "connector_id": connector_id,
                    "detected_at": _iso(captured),
                    "change_type": change_type,
                    "material_change": material,
                    "previous_snapshot_id": previous.get("snapshot_id"),
                    "current_snapshot_id": snapshot_id,
                    "previous_payload_digest": previous.get("payload_digest"),
                    "current_payload_digest": payload_digest,
                    "previous_source_timestamp": previous.get("source_timestamp"),
                    "current_source_timestamp": source_timestamp or None,
                    **comparison,
                }
                _append_jsonl(self.change_path, change_event)
                if same_period_revision or explicit_revision:
                    revision_event = {
                        "schema": REVISION_SCHEMA,
                        "version": RELEASE_VERSION,
                        "revision_id": f"revision-{uuid4().hex[:18]}",
                        "dataset_id": dataset_id,
                        "connector_id": connector_id,
                        "detected_at": _iso(captured),
                        "source_timestamp": source_timestamp or previous.get("source_timestamp"),
                        "previous_source_revision_id": previous.get("source_revision_id"),
                        "current_source_revision_id": source_revision_id or None,
                        "previous_snapshot_id": previous.get("snapshot_id"),
                        "current_snapshot_id": snapshot_id,
                        "change_id": change_event["change_id"],
                        "revision_basis": "explicit_source_revision" if explicit_revision else "same_source_period_payload_changed",
                    }
                    _append_jsonl(self.revision_path, revision_event)

        return {
            "ok": True,
            "version": RELEASE_VERSION,
            "dataset_id": dataset_id,
            "status": change_type,
            "snapshot_created": True,
            "snapshot_id": snapshot_id,
            "payload_digest": payload_digest,
            "change_id": change_event.get("change_id") if change_event else None,
            "revision_id": revision_event.get("revision_id") if revision_event else None,
            "material_change": material,
            "change_ratio": comparison["change_ratio"],
            "deduplicated": False,
        }

    def snapshots(
        self,
        *,
        dataset_id: str = "",
        connector_id: str = "",
        limit: int = 100,
        public: bool = True,
    ) -> Dict[str, Any]:
        rows = self._snapshot_rows()
        if dataset_id:
            rows = [row for row in rows if row.get("dataset_id") == dataset_id]
        if connector_id:
            rows = [row for row in rows if row.get("connector_id") == connector_id]
        rows = list(reversed(rows[-max(1, min(int(limit), 1000)):]))
        if public:
            rows = [{key: value for key, value in row.items() if key not in {"storage_path", "execution_id", "note"}} for row in rows]
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(rows),
            "snapshots": rows,
        }

    def snapshot(self, snapshot_id: str, *, include_payload: bool = False) -> Dict[str, Any]:
        row = next((item for item in self._snapshot_rows() if item.get("snapshot_id") == snapshot_id), None)
        if not row:
            raise KeyError(snapshot_id)
        result: Dict[str, Any] = {"ok": True, "version": RELEASE_VERSION, "snapshot": deepcopy(row)}
        if include_payload:
            envelope = self._load_envelope(row)
            result["payload"] = envelope.get("payload")
            result["integrity_verified"] = True
        else:
            result["snapshot"].pop("storage_path", None)
            result["snapshot"].pop("execution_id", None)
        return result

    def changes(self, *, dataset_id: str = "", material_only: bool = False, limit: int = 100) -> Dict[str, Any]:
        rows = self._change_rows()
        if dataset_id:
            rows = [row for row in rows if row.get("dataset_id") == dataset_id]
        if material_only:
            rows = [row for row in rows if row.get("material_change")]
        rows = list(reversed(rows[-max(1, min(int(limit), 1000)):]))
        return {
            "ok": True,
            "schema": CHANGE_SCHEMA,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(rows),
            "changes": rows,
        }

    def revisions(self, *, dataset_id: str = "", limit: int = 100) -> Dict[str, Any]:
        rows = self._revision_rows()
        if dataset_id:
            rows = [row for row in rows if row.get("dataset_id") == dataset_id]
        rows = list(reversed(rows[-max(1, min(int(limit), 1000)):]))
        return {
            "ok": True,
            "schema": REVISION_SCHEMA,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "count": len(rows),
            "revisions": rows,
        }

    def datasets(self, *, public: bool = True) -> Dict[str, Any]:
        snapshots = self._snapshot_rows()
        changes = self._change_rows()
        revisions = self._revision_rows()
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in snapshots:
            grouped.setdefault(str(row.get("dataset_id") or "unknown"), []).append(row)
        rows: List[Dict[str, Any]] = []
        for dataset_id, items in sorted(grouped.items()):
            source_dates = [_parse_iso(item.get("source_timestamp")) for item in items]
            valid_source_dates = [value for value in source_dates if value]
            connector_id = str(items[-1].get("connector_id") or "")
            row = {
                "dataset_id": dataset_id,
                "connector_id": connector_id,
                "name": dataset_id.replace("-", " ").title(),
                "snapshot_count": len(items),
                "first_seen_at": items[0].get("captured_at"),
                "last_seen_at": items[-1].get("captured_at"),
                "source_period_start": _iso(min(valid_source_dates)) if valid_source_dates else None,
                "source_period_end": _iso(max(valid_source_dates)) if valid_source_dates else None,
                "latest_snapshot_id": items[-1].get("snapshot_id"),
                "latest_payload_digest": items[-1].get("payload_digest"),
                "latest_record_count": items[-1].get("record_count", 0),
                "latest_change_type": items[-1].get("change_type"),
                "change_count": sum(1 for item in changes if item.get("dataset_id") == dataset_id),
                "revision_count": sum(1 for item in revisions if item.get("dataset_id") == dataset_id),
                "freshness_state": "archived" if items else "empty",
                "public_note": "Historical coverage reflects archived accepted snapshots and does not imply continuous or complete source coverage.",
            }
            if not public:
                row["latest_storage_path"] = items[-1].get("storage_path")
            rows.append(row)
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "dataset_count": len(rows),
            "datasets": rows,
        }

    def series(self, dataset_id: str, *, metric: str = "", limit: int = 120) -> Dict[str, Any]:
        rows = [row for row in self._snapshot_rows() if row.get("dataset_id") == dataset_id]
        rows = rows[-max(1, min(int(limit), self.settings.historical_archive_public_series_limit)):]
        if not rows:
            return {
                "ok": True,
                "schema": SCHEMA_VERSION,
                "version": RELEASE_VERSION,
                "dataset_id": dataset_id,
                "metric": metric or "record_count",
                "available_metrics": [],
                "count": 0,
                "observations": [],
                "coverage": {"start": None, "end": None},
            }
        latest_payload = self._load_envelope(rows[-1]).get("payload", {})
        numeric_fields = [
            key
            for key, value in _flatten(latest_payload).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ][:100]
        chosen = metric or "record_count"
        observations = []
        for row in rows:
            value: Any = row.get("record_count")
            if metric:
                payload = self._load_envelope(row).get("payload", {})
                value = _get_path(payload, metric)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            observations.append({
                "snapshot_id": row.get("snapshot_id"),
                "captured_at": row.get("captured_at"),
                "source_timestamp": row.get("source_timestamp"),
                "value": value,
                "material_change": row.get("material_change", False),
            })
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "dataset_id": dataset_id,
            "metric": chosen,
            "available_metrics": numeric_fields,
            "count": len(observations),
            "observations": observations,
            "coverage": {
                "start": observations[0]["captured_at"] if observations else None,
                "end": observations[-1]["captured_at"] if observations else None,
            },
            "methodology": "Values are read from immutable accepted snapshots. Missing, non-numeric, and incomparable values are omitted rather than imputed.",
        }

    def compare_snapshots(self, previous_snapshot_id: str, current_snapshot_id: str) -> Dict[str, Any]:
        previous = self.snapshot(previous_snapshot_id, include_payload=True)
        current = self.snapshot(current_snapshot_id, include_payload=True)
        if previous["snapshot"].get("dataset_id") != current["snapshot"].get("dataset_id"):
            raise ValueError("Snapshots must belong to the same dataset.")
        comparison = self._compare(previous["payload"], current["payload"])
        return {
            "ok": True,
            "schema": CHANGE_SCHEMA,
            "version": RELEASE_VERSION,
            "dataset_id": previous["snapshot"].get("dataset_id"),
            "previous_snapshot_id": previous_snapshot_id,
            "current_snapshot_id": current_snapshot_id,
            **comparison,
        }

    def retention(
        self,
        *,
        dry_run: bool = True,
        dataset_id: str = "",
        retention_days: Optional[int] = None,
        max_snapshots: Optional[int] = None,
    ) -> Dict[str, Any]:
        now = self.now_fn()
        days = max(1, int(retention_days or self.settings.historical_archive_default_retention_days))
        maximum = max(2, int(max_snapshots or self.settings.historical_archive_max_snapshots_per_dataset))
        minimum = max(1, int(self.policy.get("minimum_snapshots_to_keep", 2)))
        rows = self._snapshot_rows()
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            if dataset_id and row.get("dataset_id") != dataset_id:
                continue
            grouped.setdefault(str(row.get("dataset_id") or "unknown"), []).append(row)
        candidate_ids: set[str] = set()
        cutoff = now - timedelta(days=days)
        for items in grouped.values():
            protected = {item.get("snapshot_id") for item in items[-minimum:]}
            excess_count = max(0, len(items) - maximum)
            for index, item in enumerate(items):
                snapshot_id = str(item.get("snapshot_id") or "")
                captured = _parse_iso(item.get("captured_at"))
                over_count = index < excess_count
                over_age = bool(captured and captured < cutoff)
                if snapshot_id and snapshot_id not in protected and (over_count or over_age):
                    candidate_ids.add(snapshot_id)
        candidates = [row for row in rows if row.get("snapshot_id") in candidate_ids]
        removed = 0
        if not dry_run and candidates:
            with _LOCK:
                kept = [row for row in rows if row.get("snapshot_id") not in candidate_ids]
                for row in candidates:
                    relative = str(row.get("storage_path") or "")
                    if relative:
                        try:
                            (self.root_path / relative).unlink(missing_ok=True)
                        except OSError:
                            continue
                    removed += 1
                _rewrite_jsonl(self.index_path, kept)
                _append_jsonl(self.retention_log_path, {
                    "schema": SCHEMA_VERSION,
                    "version": RELEASE_VERSION,
                    "applied_at": _iso(now),
                    "retention_days": days,
                    "max_snapshots_per_dataset": maximum,
                    "removed_snapshot_ids": sorted(candidate_ids),
                })
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(now),
            "dry_run": bool(dry_run),
            "retention_days": days,
            "max_snapshots_per_dataset": maximum,
            "candidate_count": len(candidates),
            "removed_count": removed,
            "candidates": [
                {
                    "snapshot_id": row.get("snapshot_id"),
                    "dataset_id": row.get("dataset_id"),
                    "captured_at": row.get("captured_at"),
                }
                for row in candidates[:500]
            ],
            "boundary": "Retention never removes the newest protected snapshots for a dataset. Change and revision receipts remain as audit metadata.",
        }

    def export_bundle(self, dataset_id: str, *, include_payloads: bool = False, limit: int = 500) -> Dict[str, Any]:
        rows = [row for row in self._snapshot_rows() if row.get("dataset_id") == dataset_id]
        rows = rows[-max(1, min(int(limit), 1000)):]
        snapshots = []
        for row in rows:
            item = {key: value for key, value in row.items() if key != "storage_path"}
            if include_payloads:
                item["payload"] = self._load_envelope(row).get("payload")
            snapshots.append(item)
        bundle = {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "exported_at": _iso(self.now_fn()),
            "dataset_id": dataset_id,
            "snapshot_count": len(snapshots),
            "payloads_included": bool(include_payloads),
            "snapshots": snapshots,
            "changes": [item for item in self._change_rows() if item.get("dataset_id") == dataset_id],
            "revisions": [item for item in self._revision_rows() if item.get("dataset_id") == dataset_id],
            "governance": [
                "Archived payloads are sanitized before persistence.",
                "Digest verification detects changes to stored canonical payloads but does not prove upstream factual accuracy.",
                "Source revisions are distinguished from newly observed real-world changes when the evidence permits.",
            ],
        }
        return {"ok": True, "bundle": bundle, "bundle_sha256": _digest(bundle)}

    def restore_preview(self, snapshot_id: str) -> Dict[str, Any]:
        item = self.snapshot(snapshot_id, include_payload=True)
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "snapshot": item["snapshot"],
            "payload": item["payload"],
            "integrity_verified": item["integrity_verified"],
            "restore_applied": False,
            "boundary": "This is a verified restoration preview. It does not overwrite a live connector dataset or current application state.",
        }

    def public_summary(self) -> Dict[str, Any]:
        datasets = self.datasets(public=True)
        changes = self.changes(limit=50)
        revisions = self.revisions(limit=50)
        snapshot_count = sum(item.get("snapshot_count", 0) for item in datasets["datasets"])
        material_changes = sum(1 for item in changes["changes"] if item.get("material_change"))
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "title": "Historical Archive and Temporal Change Intelligence",
            "summary": "Versioned public-data snapshots, historical coverage, detected changes, and source-revision metadata across accepted connector datasets.",
            "data_state": "archived_public_metadata",
            "counts": {
                "datasets": datasets["dataset_count"],
                "snapshots": snapshot_count,
                "changes": changes["count"],
                "material_changes": material_changes,
                "source_revisions": revisions["count"],
            },
            "connectors": datasets["datasets"],
            "governance": [
                "A source correction is not presented as a new real-world event when it can be identified as a revision.",
                "Historical coverage can contain gaps because connectors have different publication schedules and availability.",
                "Public endpoints expose snapshot and change metadata, not archived payload bodies or credentials.",
                "No missing historical values are silently imputed.",
            ],
            "recommended_shortcode": "[sc_public_temporal_intelligence]",
            "endpoints": {
                "datasets": "/public/history/datasets",
                "changes": "/public/history/changes",
                "revisions": "/public/history/revisions",
                "series": "/public/history/datasets/{dataset_id}/series",
            },
        }

    def control_center(self) -> Dict[str, Any]:
        datasets = self.datasets(public=False)
        snapshots = self.snapshots(limit=50, public=False)
        changes = self.changes(limit=50)
        revisions = self.revisions(limit=50)
        retention = self.retention(dry_run=True)
        return {
            "ok": True,
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "generated_at": _iso(self.now_fn()),
            "title": "Historical Archive and Temporal Change Intelligence Control Center",
            "enabled": self.settings.historical_archive_enabled,
            "capture_on_ingest": self.settings.historical_archive_capture_on_ingest,
            "counts": {
                "datasets": datasets["dataset_count"],
                "snapshots": sum(item.get("snapshot_count", 0) for item in datasets["datasets"]),
                "changes": changes["count"],
                "revisions": revisions["count"],
                "retention_candidates": retention["candidate_count"],
            },
            "paths": {
                "root": str(self.root_path),
                "index": str(self.index_path),
                "changes": str(self.change_path),
                "revisions": str(self.revision_path),
                "retention_log": str(self.retention_log_path),
                "policy": str(self.policy_path),
            },
            "datasets": datasets["datasets"],
            "recent_snapshots": snapshots["snapshots"],
            "recent_changes": changes["changes"],
            "recent_revisions": revisions["revisions"],
            "retention_preview": retention,
            "governance": [
                "Accepted connector payloads are sanitized, size-limited, canonicalized, and SHA-256 digested before archival.",
                "Duplicate payloads are deduplicated unless an administrator explicitly forces a snapshot.",
                "Restoration is preview-only in v3.10.0; no endpoint overwrites live application state.",
                "The file-backed default requires a persistent disk path for history to survive ephemeral host replacement.",
            ],
        }
