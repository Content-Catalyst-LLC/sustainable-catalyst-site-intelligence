from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import os

VERSION = "1.18.1"
ACTOR = "site-intelligence-v1.18.0"
SOURCE_ENTITY_WORLD_BANK = "sc:source:world-bank-open-data"
SOFTWARE_ENTITY = "sc:product:site-intelligence"

_queue_lock = Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    text = value if isinstance(value, str) else canonical_json(value)
    return sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    digest = sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:24]
    return f"sc:{prefix}:{digest}"


@dataclass(frozen=True)
class CoreSettings:
    enabled: bool
    base_url: str
    write_api_key: str
    public_api_key: str
    timeout_seconds: int
    queue_path: str
    public_evidence_base_url: str

    @classmethod
    def from_environment(cls) -> "CoreSettings":
        enabled = os.getenv("SC_SI_PLATFORM_CORE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        return cls(
            enabled=enabled,
            base_url=os.getenv("SC_SI_PLATFORM_CORE_URL", "").rstrip("/"),
            write_api_key=os.getenv("SC_SI_PLATFORM_CORE_WRITE_API_KEY", ""),
            public_api_key=os.getenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY", ""),
            timeout_seconds=max(1, min(30, int(os.getenv("SC_SI_PLATFORM_CORE_TIMEOUT_SECONDS", "5")))),
            queue_path=os.getenv("SC_SI_PLATFORM_CORE_QUEUE_PATH", "backend/data/platform_core_queue.jsonl"),
            public_evidence_base_url=os.getenv("SC_SI_PLATFORM_CORE_PUBLIC_EVIDENCE_URL", "").rstrip("/"),
        )


class PlatformCoreClient:
    """Best-effort client for Platform Core v2.5.0 write contracts.

    Platform Core remains the system of record. Site Intelligence does not
    expose write credentials to WordPress or the browser. Failed writes are
    placed in a local JSONL queue for later replay.
    """

    def __init__(self, settings: CoreSettings | None = None):
        self.settings = settings or CoreSettings.from_environment()

    @property
    def configured(self) -> bool:
        return bool(self.settings.enabled and self.settings.base_url and self.settings.write_api_key)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("platform_core_not_configured")
        body = None if payload is None else canonical_json(payload).encode("utf-8")
        request = Request(
            f"{self.settings.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-SC-API-Key": self.settings.write_api_key,
                "User-Agent": f"Sustainable-Catalyst-Site-Intelligence/{VERSION}",
            },
        )
        with urlopen(request, timeout=self.settings.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def _queue(self, method: str, path: str, payload: dict[str, Any], reason: str) -> None:
        queue_path = Path(self.settings.queue_path)
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        item = {
            "queued_at": utc_now(),
            "method": method,
            "path": path,
            "payload": payload,
            "reason": reason[:500],
            "attempts": 0,
            "integration_version": VERSION,
        }
        with _queue_lock:
            with queue_path.open("a", encoding="utf-8") as handle:
                handle.write(canonical_json(item) + "\n")

    def post_or_queue(self, path: str, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        if not self.configured:
            return None, "disabled"
        try:
            return self._request("POST", path, payload), "recorded"
        except HTTPError as exc:
            # Stable IDs make 409 conflicts safe to treat as already recorded.
            if exc.code == 409:
                return {"id": payload.get("id"), "existing": True}, "existing"
            self._queue("POST", path, payload, f"http_{exc.code}")
            return None, "queued"
        except (URLError, TimeoutError, OSError, RuntimeError) as exc:
            self._queue("POST", path, payload, str(exc))
            return None, "queued"

    def replay_queue(self, limit: int = 100) -> dict[str, Any]:
        queue_path = Path(self.settings.queue_path)
        if not queue_path.exists():
            return {"ok": True, "processed": 0, "recorded": 0, "remaining": 0}
        with _queue_lock:
            lines = [line for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            pending = [json.loads(line) for line in lines]
            to_process = pending[:limit]
            untouched = pending[limit:]
            failed = []
            recorded = 0
            for item in to_process:
                try:
                    self._request(item["method"], item["path"], item["payload"])
                    recorded += 1
                except HTTPError as exc:
                    if exc.code == 409:
                        recorded += 1
                    else:
                        item["attempts"] = int(item.get("attempts", 0)) + 1
                        item["reason"] = f"http_{exc.code}"
                        failed.append(item)
                except Exception as exc:
                    item["attempts"] = int(item.get("attempts", 0)) + 1
                    item["reason"] = str(exc)[:500]
                    failed.append(item)
            remaining = failed + untouched
            if remaining:
                queue_path.write_text("\n".join(canonical_json(item) for item in remaining) + "\n", encoding="utf-8")
            else:
                queue_path.unlink(missing_ok=True)
        return {
            "ok": True,
            "processed": len(to_process),
            "recorded": recorded,
            "remaining": len(remaining),
        }

    def queue_status(self) -> dict[str, Any]:
        queue_path = Path(self.settings.queue_path)
        if not queue_path.exists():
            return {"queued_records": 0, "queue_path": self.settings.queue_path}
        count = sum(1 for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip())
        return {"queued_records": count, "queue_path": self.settings.queue_path}

    def record_indicator_lineage(
        self,
        *,
        country_code: str,
        country_name: str,
        indicator_id: str,
        indicator_key: str,
        indicator_label: str,
        canonical_url: str,
        retrieved_at: str,
        raw_payload: Any,
        latest: dict[str, Any],
        series: list[dict[str, Any]],
        source_name: str = "World Bank Open Data",
    ) -> dict[str, Any]:
        snapshot_id = stable_id("snapshot", "world-bank", country_code, indicator_id, content_hash(raw_payload))
        activity_id = stable_id("activity", "normalize-world-bank", country_code, indicator_id, retrieved_at[:10])
        evidence_id = stable_id(
            "evidence",
            country_code,
            indicator_id,
            latest.get("year"),
            latest.get("value"),
            snapshot_id,
        )
        subject_entity_id = f"sc:country:{country_code.lower()}"

        snapshot_payload = {
            "id": snapshot_id,
            "source_entity_id": SOURCE_ENTITY_WORLD_BANK,
            "canonical_url": canonical_url,
            "title": f"{country_name} — {indicator_label}",
            "publisher": source_name,
            "retrieved_at": retrieved_at,
            "media_type": "application/json",
            "content": canonical_json(raw_payload),
            "metadata": {
                "product": "site-intelligence",
                "product_version": VERSION,
                "country_code": country_code,
                "indicator_id": indicator_id,
                "indicator_key": indicator_key,
                "connector": "world-bank-open-data",
                "record_count": len(series),
                "freshness_state": "live",
            },
            "actor": ACTOR,
        }
        snapshot, snapshot_state = self.post_or_queue("/v1/source-snapshots", snapshot_payload)

        activity_payload = {
            "id": activity_id,
            "activity_type": "source_normalization",
            "name": f"Normalize {indicator_id} for {country_code}",
            "description": "Remove null observations, preserve reporting years, sort chronologically, and select the latest valid public record.",
            "agent": ACTOR,
            "software_entity_id": SOFTWARE_ENTITY,
            "started_at": retrieved_at,
            "ended_at": utc_now(),
            "parameters": {
                "country_code": country_code,
                "indicator_id": indicator_id,
                "selection_rule": "latest_non_null_observation",
                "preserve_reporting_year": True,
                "impute_missing_values": False,
            },
            "environment": {
                "service": "site-intelligence",
                "version": VERSION,
                "runtime": "python",
            },
            "status": "completed",
            "metadata": {
                "source_snapshot_id": snapshot_id,
                "series_points": len(series),
            },
        }
        activity, activity_state = self.post_or_queue("/v1/provenance/activities", activity_payload)

        # Record explicit used/generated links.
        self.post_or_queue(
            f"/v1/provenance/activities/{activity_id}/links",
            {
                "role": "used",
                "object_type": "source_snapshot",
                "object_id": snapshot_id,
                "metadata": {"indicator_id": indicator_id},
                "actor": ACTOR,
            },
        )
        self.post_or_queue(
            f"/v1/provenance/activities/{activity_id}/links",
            {
                "role": "generated",
                "object_type": "evidence_record",
                "object_id": evidence_id,
                "metadata": {"country_code": country_code, "indicator_id": indicator_id},
                "actor": ACTOR,
            },
        )

        evidence_payload = {
            "id": evidence_id,
            "evidence_type": "public_indicator_observation",
            "stance": "contextualizes",
            "subject_entity_id": subject_entity_id,
            "source_entity_id": SOURCE_ENTITY_WORLD_BANK,
            "source_snapshot_id": snapshot_id,
            "statement": (
                f"{indicator_label} for {country_name}: {latest.get('value')} "
                f"{latest.get('unit') or ''} ({latest.get('year')})."
            ).strip(),
            "methodology": "Latest non-null World Bank observation; reporting year and unit preserved; no imputation.",
            "confidence": 0.98,
            "review_status": "machine-validated",
            "provenance": {
                "activity_id": activity_id,
                "selection_rule": "latest_non_null_observation",
                "connector_version": VERSION,
            },
            "metadata": {
                "country_code": country_code,
                "indicator_id": indicator_id,
                "indicator_key": indicator_key,
                "indicator_label": indicator_label,
                "value": latest.get("value"),
                "unit": latest.get("unit"),
                "reporting_year": latest.get("year"),
                "retrieved_at": retrieved_at,
                "public": True,
            },
            "actor": ACTOR,
        }
        evidence, evidence_state = self.post_or_queue("/v1/evidence-records", evidence_payload)

        public_base = self.settings.public_evidence_base_url or self.settings.base_url
        return {
            "platform_core_enabled": self.settings.enabled,
            "platform_core_state": evidence_state if evidence_state != "disabled" else snapshot_state,
            "source_snapshot_id": snapshot_id,
            "provenance_activity_id": activity_id,
            "evidence_id": evidence_id,
            "verification_url": f"{public_base}/v1/evidence-records/{evidence_id}" if public_base else None,
            "snapshot_state": snapshot_state,
            "activity_state": activity_state,
            "evidence_state": evidence_state,
        }


def platform_core_status() -> dict[str, Any]:
    client = PlatformCoreClient()
    return {
        "ok": True,
        "version": VERSION,
        "enabled": client.settings.enabled,
        "configured": client.configured,
        "base_url_configured": bool(client.settings.base_url),
        "write_key_configured": bool(client.settings.write_api_key),
        "public_api_key_configured": bool(client.settings.public_api_key),
        "timeout_seconds": client.settings.timeout_seconds,
        **client.queue_status(),
        "write_credentials_exposed_publicly": False,
    }
