from __future__ import annotations

from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import io
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import threading
import time
from typing import Any, Callable, Iterator
from uuid import uuid4
import zipfile

from .config import Settings

RELEASE_VERSION = "3.19.0"
SCHEMA_VERSION = "sc-site-intelligence-production-governance/1.0"
MIGRATION_VERSION = 3
ALLOWED_SCOPES = {
    "governance:read",
    "governance:write",
    "audit:read",
    "audit:write",
    "backup:read",
    "backup:write",
    "privacy:read",
    "privacy:write",
    "jobs:read",
    "jobs:write",
}
PRIVACY_REQUEST_TYPES = {"access", "export", "correct", "restrict", "delete"}
PRIVACY_STATES = {"received", "verified", "in_review", "completed", "rejected"}
JOB_STATES = {"queued", "leased", "completed", "failed", "cancelled"}
_SECRET_MARKERS = ("token", "secret", "password", "authorization", "api_key", "cookie", "session", "private_key")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_text(value: Any, limit: int = 4000) -> str:
    return str(value or "").replace("\x00", "").strip()[:limit]


def _safe_id(value: Any, fallback: str = "record") -> str:
    raw = _safe_text(value, 240)
    cleaned = "".join(ch if ch.isalnum() or ch in "._:@/-" else "-" for ch in raw).strip("-:./")
    return cleaned or fallback


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower().replace("-", "_")
            output[str(key)] = "[redacted]" if any(marker in lowered for marker in _SECRET_MARKERS) else _redact(item)
        return output
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class SlidingWindowRateLimiter:
    """Small in-process limiter for control-plane endpoints.

    It deliberately does not claim distributed enforcement. Deployments with more
    than one worker should place an external gateway or shared limiter in front.
    """

    def __init__(self, limit: int, window_seconds: int, now_fn: Callable[[], float] = time.time) -> None:
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.now_fn = now_fn
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> dict[str, Any]:
        now = float(self.now_fn())
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            allowed = len(bucket) < self.limit
            if allowed:
                bucket.append(now)
            remaining = max(0, self.limit - len(bucket))
            retry_after = 0 if allowed or not bucket else max(1, int(self.window_seconds - (now - bucket[0])))
        return {"allowed": allowed, "remaining": remaining, "retry_after_seconds": retry_after, "distributed": False}


class ProductionGovernanceCenter:
    """Security, privacy, governance, and production-scale control plane.

    The implementation uses SQLite for a zero-cost durable mode, explicit schema
    migrations, hashed scoped API keys, a hash-chained audit log, preview-first
    retention, verified backups, and a bounded job queue. It does not claim that
    local rate limits or queues are distributed across multiple application workers.
    """

    def __init__(self, settings: Settings, now_fn: Callable[[], datetime] = _utc_now) -> None:
        self.settings = settings
        self.now_fn = now_fn
        self.database_path = _resolve(settings.production_database_path)
        self.backup_dir = _resolve(settings.production_backup_path)
        self.policy_path = _resolve(settings.production_governance_policy_path)
        self.policy = self._read_json(self.policy_path, {})
        self.max_records = settings.production_governance_max_records
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.apply_migrations()

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def apply_migrations(self) -> dict[str, Any]:
        migrations: list[tuple[int, list[str]]] = [
            (1, [
                "CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, sha256 TEXT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS api_keys(key_id TEXT PRIMARY KEY, label TEXT NOT NULL, prefix TEXT NOT NULL, secret_hash TEXT NOT NULL, scopes_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT, last_used_at TEXT)",
                "CREATE TABLE IF NOT EXISTS audit_events(event_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL UNIQUE, occurred_at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, outcome TEXT NOT NULL, metadata_json TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS privacy_requests(request_id TEXT PRIMARY KEY, request_type TEXT NOT NULL, subject_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, due_at TEXT NOT NULL, notes TEXT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS retention_events(event_id TEXT PRIMARY KEY, category TEXT NOT NULL, cutoff_at TEXT NOT NULL, preview_count INTEGER NOT NULL, deleted_count INTEGER NOT NULL, confirmed INTEGER NOT NULL, created_at TEXT NOT NULL, sha256 TEXT NOT NULL)",
            ]),
            (2, [
                "CREATE TABLE IF NOT EXISTS backup_receipts(backup_id TEXT PRIMARY KEY, path TEXT NOT NULL, created_at TEXT NOT NULL, database_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, verified INTEGER NOT NULL, restore_performed INTEGER NOT NULL DEFAULT 0)",
                "CREATE TABLE IF NOT EXISTS job_queue(job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, payload_json TEXT NOT NULL, status TEXT NOT NULL, priority INTEGER NOT NULL, attempts INTEGER NOT NULL, max_attempts INTEGER NOT NULL, available_at TEXT NOT NULL, lease_expires_at TEXT, leased_by TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, result_json TEXT NOT NULL)",
                "CREATE INDEX IF NOT EXISTS idx_job_queue_status_available ON job_queue(status, available_at, priority)",
            ]),
            (3, [
                "CREATE TABLE IF NOT EXISTS deployment_receipts(receipt_id TEXT PRIMARY KEY, release_version TEXT NOT NULL, commit_sha TEXT NOT NULL, environment TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, checks_json TEXT NOT NULL, sha256 TEXT NOT NULL)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at ON audit_events(occurred_at)",
                "CREATE INDEX IF NOT EXISTS idx_privacy_requests_status ON privacy_requests(status, due_at)",
            ]),
        ]
        applied: list[int] = []
        with sqlite3.connect(self.database_path, timeout=10) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, sha256 TEXT NOT NULL)")
            existing = {int(row[0]) for row in connection.execute("SELECT version FROM schema_migrations")}
            for version, statements in migrations:
                if version in existing:
                    continue
                for statement in statements:
                    connection.execute(statement)
                receipt = {"version": version, "statements": statements}
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at, sha256) VALUES(?,?,?)",
                    (version, _iso(self.now_fn()), _digest(receipt)),
                )
                applied.append(version)
            connection.commit()
        return {"schema": SCHEMA_VERSION, "target_version": MIGRATION_VERSION, "applied": applied, "current_version": self.migration_status()["current_version"]}

    def migration_status(self) -> dict[str, Any]:
        with sqlite3.connect(self.database_path) as connection:
            rows = list(connection.execute("SELECT version, applied_at, sha256 FROM schema_migrations ORDER BY version"))
        return {
            "current_version": max([int(row[0]) for row in rows], default=0),
            "target_version": MIGRATION_VERSION,
            "migrations": [{"version": row[0], "applied_at": row[1], "sha256": row[2]} for row in rows],
            "up_to_date": bool(rows) and int(rows[-1][0]) == MIGRATION_VERSION,
        }

    def create_api_key(self, request: dict[str, Any]) -> dict[str, Any]:
        label = _safe_text(request.get("label"), 200)
        if not label:
            raise ValueError("label is required")
        scopes = sorted(set(str(scope) for scope in request.get("scopes", []) if scope in ALLOWED_SCOPES))
        if not scopes:
            raise ValueError("At least one supported scope is required")
        expires_at = _parse_dt(request.get("expires_at"))
        if expires_at and expires_at <= self.now_fn():
            raise ValueError("expires_at must be in the future")
        key_id = f"key-{uuid4().hex[:16]}"
        secret = secrets.token_urlsafe(32)
        token = f"scsi_{key_id}_{secret}"
        prefix = token[:22]
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO api_keys(key_id,label,prefix,secret_hash,scopes_json,status,created_at,expires_at,last_used_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (key_id, label, prefix, hashlib.sha256(token.encode()).hexdigest(), json.dumps(scopes), "active", _iso(self.now_fn()), _iso(expires_at) if expires_at else None, None),
            )
        self.record_audit("api_key.created", "system", "api_key", key_id, "success", {"label": label, "scopes": scopes})
        return {"schema": "sc-scoped-api-key/1.0", "key_id": key_id, "token": token, "prefix": prefix, "scopes": scopes, "expires_at": _iso(expires_at) if expires_at else None, "shown_once": True}

    def list_api_keys(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = list(connection.execute("SELECT key_id,label,prefix,scopes_json,status,created_at,expires_at,last_used_at FROM api_keys ORDER BY created_at DESC LIMIT ?", (self.max_records,)))
        return [{**dict(row), "scopes": json.loads(row["scopes_json"]), "scopes_json": None} for row in rows]

    def verify_api_key(self, token: str, required_scope: str) -> dict[str, Any]:
        token_hash = hashlib.sha256(str(token or "").encode()).hexdigest()
        with self.connection() as connection:
            rows = list(connection.execute("SELECT * FROM api_keys WHERE status='active'"))
            for row in rows:
                if not hmac.compare_digest(row["secret_hash"], token_hash):
                    continue
                expires_at = _parse_dt(row["expires_at"])
                if expires_at and expires_at <= self.now_fn():
                    return {"valid": False, "reason": "expired"}
                scopes = json.loads(row["scopes_json"])
                if required_scope not in scopes:
                    return {"valid": False, "reason": "missing_scope", "key_id": row["key_id"], "scopes": scopes}
                connection.execute("UPDATE api_keys SET last_used_at=? WHERE key_id=?", (_iso(self.now_fn()), row["key_id"]))
                return {"valid": True, "key_id": row["key_id"], "label": row["label"], "scopes": scopes}
        return {"valid": False, "reason": "unknown_key"}

    def revoke_api_key(self, key_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            cursor = connection.execute("UPDATE api_keys SET status='revoked' WHERE key_id=?", (_safe_id(key_id),))
        if not cursor.rowcount:
            raise KeyError(key_id)
        self.record_audit("api_key.revoked", "administrator", "api_key", key_id, "success", {})
        return {"key_id": key_id, "status": "revoked"}

    def record_audit(self, action: str, actor: str, resource_type: str, resource_id: str, outcome: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self.connection() as connection:
            previous = connection.execute("SELECT sequence,event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1").fetchone()
            sequence = (int(previous["sequence"]) + 1) if previous else 1
            previous_hash = str(previous["event_hash"]) if previous else "0" * 64
            row = {
                "event_id": f"audit-{uuid4().hex}",
                "sequence": sequence,
                "occurred_at": _iso(self.now_fn()),
                "actor": _safe_text(actor, 200) or "unknown",
                "action": _safe_text(action, 200),
                "resource_type": _safe_text(resource_type, 100),
                "resource_id": _safe_id(resource_id, "unknown"),
                "outcome": _safe_text(outcome, 40),
                "metadata": _redact(metadata or {}),
                "previous_hash": previous_hash,
            }
            row["event_hash"] = _digest(row)
            connection.execute(
                "INSERT INTO audit_events(event_id,sequence,occurred_at,actor,action,resource_type,resource_id,outcome,metadata_json,previous_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (row["event_id"], sequence, row["occurred_at"], row["actor"], row["action"], row["resource_type"], row["resource_id"], row["outcome"], json.dumps(row["metadata"], sort_keys=True), previous_hash, row["event_hash"]),
            )
        return row

    def audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = list(connection.execute("SELECT * FROM audit_events ORDER BY sequence DESC LIMIT ?", (max(1, min(int(limit), 1000)),)))
        return [{**dict(row), "metadata": json.loads(row["metadata_json"]), "metadata_json": None} for row in rows]

    def verify_audit_chain(self) -> dict[str, Any]:
        with self.connection() as connection:
            rows = list(connection.execute("SELECT * FROM audit_events ORDER BY sequence"))
        previous_hash = "0" * 64
        errors: list[str] = []
        for expected, row in enumerate(rows, start=1):
            payload = {
                "event_id": row["event_id"], "sequence": row["sequence"], "occurred_at": row["occurred_at"], "actor": row["actor"],
                "action": row["action"], "resource_type": row["resource_type"], "resource_id": row["resource_id"], "outcome": row["outcome"],
                "metadata": json.loads(row["metadata_json"]), "previous_hash": row["previous_hash"],
            }
            if row["sequence"] != expected:
                errors.append(f"sequence:{row['event_id']}")
            if row["previous_hash"] != previous_hash:
                errors.append(f"previous_hash:{row['event_id']}")
            if not hmac.compare_digest(row["event_hash"], _digest(payload)):
                errors.append(f"event_hash:{row['event_id']}")
            previous_hash = row["event_hash"]
        return {"valid": not errors, "event_count": len(rows), "errors": errors, "head_hash": previous_hash}

    def create_privacy_request(self, request: dict[str, Any]) -> dict[str, Any]:
        request_type = _safe_text(request.get("request_type"), 30).lower()
        if request_type not in PRIVACY_REQUEST_TYPES:
            raise ValueError("Unsupported request_type")
        subject_reference = _safe_text(request.get("subject_reference"), 500)
        if not subject_reference:
            raise ValueError("subject_reference is required")
        created_at = self.now_fn()
        row = {
            "request_id": f"privacy-{uuid4().hex[:20]}",
            "request_type": request_type,
            "subject_hash": hashlib.sha256(subject_reference.encode()).hexdigest(),
            "status": "received",
            "created_at": _iso(created_at),
            "updated_at": _iso(created_at),
            "due_at": _iso(created_at + timedelta(days=self.settings.production_privacy_request_days)),
            "notes": _safe_text(request.get("notes"), 2000),
        }
        with self.connection() as connection:
            connection.execute("INSERT INTO privacy_requests VALUES(?,?,?,?,?,?,?,?)", tuple(row.values()))
        self.record_audit("privacy_request.created", "administrator", "privacy_request", row["request_id"], "success", {"request_type": request_type})
        return {**row, "subject_reference_stored": False}

    def update_privacy_request(self, request_id: str, request: dict[str, Any]) -> dict[str, Any]:
        status = _safe_text(request.get("status"), 30).lower()
        if status not in PRIVACY_STATES:
            raise ValueError("Unsupported status")
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM privacy_requests WHERE request_id=?", (_safe_id(request_id),)).fetchone()
            if not row:
                raise KeyError(request_id)
            notes = _safe_text(request.get("notes") if "notes" in request else row["notes"], 2000)
            connection.execute("UPDATE privacy_requests SET status=?,updated_at=?,notes=? WHERE request_id=?", (status, _iso(self.now_fn()), notes, row["request_id"]))
            updated = connection.execute("SELECT * FROM privacy_requests WHERE request_id=?", (row["request_id"],)).fetchone()
        self.record_audit("privacy_request.updated", "administrator", "privacy_request", request_id, "success", {"status": status})
        return dict(updated)

    def privacy_requests(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM privacy_requests ORDER BY created_at DESC LIMIT ?", (self.max_records,))]

    def retention_preview(self, request: dict[str, Any]) -> dict[str, Any]:
        category = _safe_text(request.get("category") or "audit_events", 50)
        days = max(1, min(int(request.get("days") or self.settings.production_default_retention_days), 3650))
        cutoff = self.now_fn() - timedelta(days=days)
        table, field = {
            "audit_events": ("audit_events", "occurred_at"),
            "privacy_requests": ("privacy_requests", "updated_at"),
            "job_queue": ("job_queue", "updated_at"),
            "deployment_receipts": ("deployment_receipts", "created_at"),
        }.get(category, (None, None))
        if not table:
            raise ValueError("Unsupported retention category")
        with self.connection() as connection:
            count = int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} < ?", (_iso(cutoff),)).fetchone()[0])
        return {"category": category, "days": days, "cutoff_at": _iso(cutoff), "preview_count": count, "requires_confirm": True, "automatic_deletion": False}

    def apply_retention(self, request: dict[str, Any]) -> dict[str, Any]:
        preview = self.retention_preview(request)
        if request.get("confirm") is not True:
            raise ValueError("confirm=true is required")
        table, field = {
            "audit_events": ("audit_events", "occurred_at"),
            "privacy_requests": ("privacy_requests", "updated_at"),
            "job_queue": ("job_queue", "updated_at"),
            "deployment_receipts": ("deployment_receipts", "created_at"),
        }[preview["category"]]
        with self.connection() as connection:
            cursor = connection.execute(f"DELETE FROM {table} WHERE {field} < ?", (preview["cutoff_at"],))
            deleted = int(cursor.rowcount)
            event = {
                "event_id": f"retention-{uuid4().hex}", "category": preview["category"], "cutoff_at": preview["cutoff_at"],
                "preview_count": preview["preview_count"], "deleted_count": deleted, "confirmed": 1, "created_at": _iso(self.now_fn()),
            }
            event["sha256"] = _digest(event)
            connection.execute("INSERT INTO retention_events VALUES(?,?,?,?,?,?,?,?)", tuple(event.values()))
        return {**preview, "deleted_count": deleted, "confirmed": True, "receipt_sha256": event["sha256"]}

    def create_backup(self, request: dict[str, Any]) -> dict[str, Any]:
        label = _safe_id(request.get("label") or self.now_fn().strftime("%Y%m%d-%H%M%S"), "backup")
        backup_id = f"backup-{uuid4().hex[:16]}"
        temp_db = self.backup_dir / f"{backup_id}.sqlite3"
        archive_path = self.backup_dir / f"site-intelligence-{label}-{backup_id}.zip"
        with sqlite3.connect(self.database_path) as source, sqlite3.connect(temp_db) as destination:
            source.backup(destination)
        database_bytes = temp_db.stat().st_size
        metadata = {"schema": "sc-production-backup/1.0", "backup_id": backup_id, "release_version": RELEASE_VERSION, "created_at": _iso(self.now_fn()), "database_bytes": database_bytes, "database_sha256": hashlib.sha256(temp_db.read_bytes()).hexdigest()}
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(temp_db, arcname="production.sqlite3")
            archive.writestr("backup.json", json.dumps(metadata, indent=2, sort_keys=True))
        temp_db.unlink(missing_ok=True)
        archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        with self.connection() as connection:
            connection.execute("INSERT INTO backup_receipts VALUES(?,?,?,?,?,?,?)", (backup_id, str(archive_path), metadata["created_at"], database_bytes, archive_sha, 1, 0))
        self.record_audit("backup.created", "administrator", "backup", backup_id, "success", {"path": archive_path.name, "bytes": database_bytes})
        return {**metadata, "archive_path": str(archive_path), "archive_sha256": archive_sha, "verified": True, "restore_performed": False}

    def verify_backup(self, backup_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM backup_receipts WHERE backup_id=?", (_safe_id(backup_id),)).fetchone()
        if not row:
            raise KeyError(backup_id)
        path = Path(row["path"])
        errors: list[str] = []
        if not path.is_file():
            errors.append("archive_missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            errors.append("archive_digest_mismatch")
        else:
            try:
                with zipfile.ZipFile(path) as archive:
                    names = set(archive.namelist())
                    if {"production.sqlite3", "backup.json"} - names:
                        errors.append("archive_members_missing")
                    else:
                        metadata = json.loads(archive.read("backup.json"))
                        if metadata.get("backup_id") != backup_id:
                            errors.append("metadata_backup_id_mismatch")
            except (zipfile.BadZipFile, json.JSONDecodeError):
                errors.append("invalid_archive")
        return {"backup_id": backup_id, "valid": not errors, "errors": errors, "restore_performed": bool(row["restore_performed"]), "preview_only": True}

    def restore_preview(self, backup_id: str) -> dict[str, Any]:
        verification = self.verify_backup(backup_id)
        return {**verification, "requires_confirmed_maintenance_procedure": True, "automatic_restore": False, "database_mutated": False}

    def enqueue_job(self, request: dict[str, Any]) -> dict[str, Any]:
        job_type = _safe_id(request.get("job_type"), "job")
        now = self.now_fn()
        available_at = _parse_dt(request.get("available_at")) or now
        row = {
            "job_id": f"job-{uuid4().hex[:20]}", "job_type": job_type, "payload_json": json.dumps(_redact(request.get("payload") or {}), sort_keys=True),
            "status": "queued", "priority": max(-100, min(int(request.get("priority") or 0), 100)), "attempts": 0,
            "max_attempts": max(1, min(int(request.get("max_attempts") or 3), 20)), "available_at": _iso(available_at), "lease_expires_at": None,
            "leased_by": None, "created_at": _iso(now), "updated_at": _iso(now), "result_json": "{}",
        }
        with self.connection() as connection:
            connection.execute("INSERT INTO job_queue VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row.values()))
        return self._job_public(row)

    @staticmethod
    def _job_public(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = json.loads(data.pop("payload_json", "{}"))
        data["result"] = json.loads(data.pop("result_json", "{}"))
        return data

    def lease_job(self, worker_id: str, lease_seconds: int = 60) -> dict[str, Any] | None:
        now = self.now_fn()
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM job_queue WHERE status='queued' AND available_at<=? ORDER BY priority DESC,created_at ASC LIMIT 1",
                (_iso(now),),
            ).fetchone()
            if not row:
                return None
            lease_expires = now + timedelta(seconds=max(10, min(int(lease_seconds), 3600)))
            connection.execute("UPDATE job_queue SET status='leased',attempts=attempts+1,leased_by=?,lease_expires_at=?,updated_at=? WHERE job_id=?", (_safe_id(worker_id), _iso(lease_expires), _iso(now), row["job_id"]))
            updated = connection.execute("SELECT * FROM job_queue WHERE job_id=?", (row["job_id"],)).fetchone()
        return self._job_public(updated)

    def complete_job(self, job_id: str, request: dict[str, Any]) -> dict[str, Any]:
        status = _safe_text(request.get("status") or "completed", 20).lower()
        if status not in {"completed", "failed", "cancelled"}:
            raise ValueError("Unsupported terminal status")
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM job_queue WHERE job_id=?", (_safe_id(job_id),)).fetchone()
            if not row:
                raise KeyError(job_id)
            connection.execute("UPDATE job_queue SET status=?,result_json=?,lease_expires_at=NULL,updated_at=? WHERE job_id=?", (status, json.dumps(_redact(request.get("result") or {}), sort_keys=True), _iso(self.now_fn()), row["job_id"]))
            updated = connection.execute("SELECT * FROM job_queue WHERE job_id=?", (row["job_id"],)).fetchone()
        return self._job_public(updated)

    def queue_summary(self) -> dict[str, Any]:
        with self.connection() as connection:
            rows = list(connection.execute("SELECT status,COUNT(*) AS count FROM job_queue GROUP BY status"))
        counts = {row["status"]: row["count"] for row in rows}
        return {"counts": {state: int(counts.get(state, 0)) for state in sorted(JOB_STATES)}, "distributed": False, "persistent": True, "automatic_worker": False}

    def record_deployment(self, request: dict[str, Any]) -> dict[str, Any]:
        status = _safe_text(request.get("status") or "validated", 30)
        row = {
            "receipt_id": f"deploy-{uuid4().hex[:20]}", "release_version": _safe_text(request.get("release_version") or RELEASE_VERSION, 30),
            "commit_sha": _safe_text(request.get("commit_sha"), 80), "environment": _safe_text(request.get("environment") or self.settings.environment, 50),
            "status": status, "created_at": _iso(self.now_fn()), "checks": _redact(request.get("checks") or {}),
        }
        row["sha256"] = _digest(row)
        with self.connection() as connection:
            connection.execute("INSERT INTO deployment_receipts(receipt_id,release_version,commit_sha,environment,status,created_at,checks_json,sha256) VALUES(?,?,?,?,?,?,?,?)", (row["receipt_id"], row["release_version"], row["commit_sha"], row["environment"], row["status"], row["created_at"], json.dumps(row["checks"], sort_keys=True), row["sha256"]))
        return row

    def load_probe(self, requests: int = 250) -> dict[str, Any]:
        count = max(1, min(int(requests), 5000))
        started = time.perf_counter()
        payload = {"release": RELEASE_VERSION, "policy": self.policy.get("policy_version", "unknown")}
        for index in range(count):
            _digest({"index": index, "payload": payload})
        elapsed = max(time.perf_counter() - started, 1e-9)
        return {"requests": count, "elapsed_ms": round(elapsed * 1000, 3), "operations_per_second": round(count / elapsed, 1), "synthetic": True, "network_load_test": False}

    def diagnostics(self, public: bool = False) -> dict[str, Any]:
        migration = self.migration_status()
        audit = self.verify_audit_chain()
        queue = self.queue_summary()
        database_bytes = self.database_path.stat().st_size if self.database_path.exists() else 0
        backup_count = len(list(self.backup_dir.glob("*.zip")))
        with self.connection() as connection:
            counts = {
                "api_keys": int(connection.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]),
                "privacy_requests": int(connection.execute("SELECT COUNT(*) FROM privacy_requests").fetchone()[0]),
                "audit_events": int(connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]),
                "deployment_receipts": int(connection.execute("SELECT COUNT(*) FROM deployment_receipts").fetchone()[0]),
            }
        result = {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "status": "ready" if migration["up_to_date"] and audit["valid"] else "review",
            "storage": {"engine": "sqlite", "persistent_path_configured": self.database_path.is_absolute(), "database_bytes": database_bytes, "migration_version": migration["current_version"]},
            "audit": {"valid": audit["valid"], "event_count": audit["event_count"], "head_hash": audit["head_hash"]},
            "queue": queue,
            "backups": {"count": backup_count, "automatic_restore": False},
            "counts": counts,
            "rate_limiting": {"local_process_available": True, "distributed": False, "gateway_recommended": True},
            "privacy": {"request_deadline_days": self.settings.production_privacy_request_days, "automatic_deletion": False},
            "governance": {"human_confirmation": True, "scoped_api_keys": True, "secrets_public": False, "audit_hash_chain": True},
        }
        if public:
            result["storage"].pop("database_bytes", None)
            result["counts"].pop("api_keys", None)
            result["counts"].pop("privacy_requests", None)
        return result

    def public_summary(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "version": RELEASE_VERSION,
            "title": "Security, Privacy, Governance, and Production Scale",
            "diagnostics": self.diagnostics(public=True),
            "capabilities": [
                "versioned SQLite migrations", "scoped and hashed API keys", "hash-chained audit events", "privacy request tracking",
                "preview-first retention", "digest-verified backups", "persistent bounded job queue", "deployment receipts", "synthetic load probe",
            ],
            "boundaries": [
                "No secrets or raw key hashes are exposed publicly.", "Local rate limiting is not represented as distributed enforcement.",
                "The persistent queue does not claim an always-on worker.", "Backups are verified, but restoration remains a confirmed maintenance action.",
                "Retention never deletes records without confirm=true.",
            ],
        }

    def control_center(self) -> dict[str, Any]:
        return {
            **self.public_summary(),
            "migration_status": self.migration_status(),
            "api_keys": self.list_api_keys(),
            "privacy_requests": self.privacy_requests(),
            "audit_events": self.audit_events(50),
            "queue_summary": self.queue_summary(),
            "policy": self.policy,
        }
