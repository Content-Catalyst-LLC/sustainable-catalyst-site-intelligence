"""Zero-cost in-memory + JSON last-known-good cache for country intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

CACHE_SCHEMA_VERSION = 1
DEFAULT_FRESH_SECONDS = 6 * 60 * 60
DEFAULT_STALE_SECONDS = 7 * 24 * 60 * 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def default_cache_path() -> Path:
    configured = os.getenv("SC_SI_COUNTRY_CACHE_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / "data" / "country_last_known_good.json"


@dataclass(frozen=True)
class CacheResult:
    value: Any
    state: str
    stored_at: str | None
    age_seconds: float | None
    stale: bool


class CountryJsonCache:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_cache_path()
        self._lock = RLock()
        self._loaded = False
        self._entries: dict[str, dict[str, Any]] = {}
        self._stats = {"hits": 0, "misses": 0, "stale_hits": 0, "writes": 0, "read_errors": 0, "write_errors": 0}

    def _load(self) -> None:
        with self._lock:
            if self._loaded:
                return
            self._loaded = True
            try:
                if not self.path.exists():
                    return
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if payload.get("schema_version") != CACHE_SCHEMA_VERSION:
                    return
                entries = payload.get("entries")
                if isinstance(entries, dict):
                    self._entries = entries
            except (OSError, ValueError, TypeError):
                self._stats["read_errors"] += 1
                self._entries = {}

    def get(
        self,
        key: str,
        *,
        fresh_seconds: int = DEFAULT_FRESH_SECONDS,
        stale_seconds: int = DEFAULT_STALE_SECONDS,
        allow_stale: bool = True,
    ) -> CacheResult | None:
        self._load()
        with self._lock:
            entry = self._entries.get(key)
            if not isinstance(entry, dict):
                self._stats["misses"] += 1
                return None
            stored_at = entry.get("stored_at")
            stored_dt = parse_time(stored_at)
            if stored_dt is None:
                self._stats["misses"] += 1
                return None
            age = max(0.0, (datetime.now(timezone.utc) - stored_dt).total_seconds())
            if age <= fresh_seconds:
                self._stats["hits"] += 1
                return CacheResult(entry.get("value"), "cached", stored_at, age, False)
            if allow_stale and age <= stale_seconds:
                self._stats["stale_hits"] += 1
                return CacheResult(entry.get("value"), "stale", stored_at, age, True)
            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any) -> str:
        self._load()
        stored_at = utc_now()
        with self._lock:
            self._entries[key] = {"stored_at": stored_at, "value": value}
            self._stats["writes"] += 1
            self._persist()
        return stored_at

    def delete(self, key: str) -> None:
        self._load()
        with self._lock:
            self._entries.pop(key, None)
            self._persist()

    def clear(self) -> None:
        with self._lock:
            self._loaded = True
            self._entries = {}
            self._persist()

    def _persist(self) -> None:
        payload = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "entries": self._entries,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            temporary.replace(self.path)
        except OSError:
            self._stats["write_errors"] += 1

    def diagnostics(self) -> dict[str, Any]:
        self._load()
        with self._lock:
            size = None
            try:
                size = self.path.stat().st_size if self.path.exists() else 0
            except OSError:
                size = None
            return {
                "backend": "memory-plus-json-last-known-good",
                "path": self.path.name,
                "entry_count": len(self._entries),
                "file_size_bytes": size,
                "stats": dict(self._stats),
            }


country_cache = CountryJsonCache()
