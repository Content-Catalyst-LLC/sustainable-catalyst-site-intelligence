"""Data freshness, coverage, and source-truth contract for Site Intelligence v4.26.0."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

from .config import Settings
from .live_intelligence_source_operations_v320 import LiveIntelligenceSourceOperations
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-data-truth/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
CLASSIFICATIONS = (
    "live",
    "recently_cached",
    "historical_snapshot",
    "demonstration",
    "context_only",
    "unavailable",
)
_REQUIRED_METADATA = (
    "feed_id", "label", "provider", "endpoint", "license", "coverage",
    "default_refresh_minutes", "default_cache_ttl_minutes", "stale_after_minutes",
    "data_classification", "schema_contract", "retry_policy", "geographic_policy",
)


def _canonical_fingerprint(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(body).hexdigest()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class DataTruthCenter:
    """Build public-safe source, freshness, completeness, and schema disclosures."""

    def __init__(self, settings: Settings, operations: LiveIntelligenceSourceOperations | None = None) -> None:
        self.settings = settings
        self.operations = operations or LiveIntelligenceSourceOperations(settings)

    def _classification(self, source: Mapping[str, Any]) -> dict[str, Any]:
        declared = str(source.get("data_classification") or "context_only")
        runtime = source.get("runtime") or {}
        health = source.get("health") or {}
        effective = source.get("effective") or {}
        enabled = bool(effective.get("enabled", True))
        last_success = runtime.get("last_success_at")
        last_state = str(runtime.get("last_data_state") or "unknown")
        failures = _safe_int(runtime.get("consecutive_failures"))
        freshness = str(health.get("freshness") or "unknown")
        stale = freshness == "stale" or str(health.get("state")) == "stale"

        if not enabled:
            presentation = "unavailable"
            reason = "Source retrieval is disabled."
        elif not last_success:
            presentation = "demonstration" if self.settings.demo_mode else "unavailable"
            reason = "No successful production retrieval has been recorded; configured examples must not be presented as live." if self.settings.demo_mode else "No successful retrieval has been recorded."
        elif declared == "context_only":
            presentation = "context_only"
            reason = "The source provides research context rather than a real-time condition."
        elif declared == "historical_snapshot":
            presentation = "historical_snapshot"
            reason = "The source publishes periodic or dated observations, not a live measurement."
        elif stale:
            presentation = "historical_snapshot"
            reason = "The last known good response is older than the source freshness threshold."
        elif failures or last_state in {"cached", "fallback-suppressed", "fallback_suppressed"}:
            presentation = "recently_cached"
            reason = "The current presentation uses a disclosed last-known-good response while retrieval is degraded."
        else:
            presentation = "live"
            reason = "A successful response is within the declared freshness threshold."

        stale_marker = presentation in {"recently_cached", "historical_snapshot"} and (stale or failures > 0 or last_state == "cached")
        return {
            "declared": declared,
            "presentation": presentation,
            "live_claim_allowed": presentation == "live",
            "stale_marker_required": stale_marker,
            "reason": reason,
        }

    @staticmethod
    def _completeness(source: Mapping[str, Any]) -> dict[str, Any]:
        missing = [field for field in _REQUIRED_METADATA if source.get(field) in (None, "", [], {})]
        score = round(100 * (len(_REQUIRED_METADATA) - len(missing)) / len(_REQUIRED_METADATA), 1)
        coverage = source.get("coverage") or {}
        coverage_missing = [key for key in ("geographic", "temporal") if not coverage.get(key)]
        return {
            "required_metadata_fields": len(_REQUIRED_METADATA),
            "missing_metadata_fields": missing,
            "coverage_missing": coverage_missing,
            "score_percent": score,
            "complete": not missing and not coverage_missing,
        }

    @staticmethod
    def _schema(source: Mapping[str, Any]) -> dict[str, Any]:
        contract = source.get("schema_contract") or {}
        expected = _canonical_fingerprint(contract)
        runtime = source.get("runtime") or {}
        observed = str(runtime.get("observed_schema_fingerprint") or "")
        if not observed:
            status = "not_observed"
        elif observed == expected:
            status = "matched"
        else:
            status = "changed"
        return {
            "record_type": contract.get("record_type"),
            "required_fields": list(contract.get("required_fields") or []),
            "expected_fingerprint": expected,
            "observed_fingerprint": observed or None,
            "status": status,
            "last_checked_at": runtime.get("last_schema_check_at"),
            "last_change_at": runtime.get("last_schema_change_at"),
            "change_policy": contract.get("change_policy", "flag_and_review"),
        }

    @staticmethod
    def _resilience(source: Mapping[str, Any]) -> dict[str, Any]:
        policy = source.get("retry_policy") or {}
        runtime = source.get("runtime") or {}
        failures = _safe_int(runtime.get("consecutive_failures"))
        threshold = max(1, _safe_int(policy.get("circuit_breaker_failures"), 3))
        circuit_state = "open" if failures >= threshold else "watch" if failures else "closed"
        return {
            "retry_strategy": policy.get("strategy", "bounded_exponential"),
            "maximum_attempts": _safe_int(policy.get("maximum_attempts"), 3),
            "circuit_breaker_threshold": threshold,
            "circuit_breaker_state": circuit_state,
            "consecutive_failures": failures,
            "last_known_good_available": bool(runtime.get("last_success_at")),
            "fallback_may_claim_live": bool(policy.get("automatic_fallback_claims_live", False)),
        }

    def _row(self, source: Mapping[str, Any]) -> dict[str, Any]:
        runtime = source.get("runtime") or {}
        effective = source.get("effective") or {}
        health = source.get("health") or {}
        endpoint = source.get("endpoint") or {}
        classification = self._classification(source)
        completeness = self._completeness(source)
        schema = self._schema(source)
        resilience = self._resilience(source)
        return {
            "feed_id": source.get("feed_id"),
            "label": source.get("label"),
            "publisher": source.get("provider"),
            "category": source.get("category"),
            "endpoint": {
                "url": endpoint.get("url"),
                "access": endpoint.get("access", "public"),
                "credentials_required": bool(endpoint.get("credentials_required", False)),
            },
            "license": source.get("license") or {},
            "coverage": source.get("coverage") or {},
            "geographic_policy": source.get("geographic_policy") or {},
            "runtime": {"country_record_counts": (runtime.get("country_record_counts") or {}) if isinstance(runtime.get("country_record_counts"), Mapping) else {}},
            "refresh_policy": {
                "refresh_minutes": _safe_int(effective.get("refresh_minutes"), _safe_int(source.get("default_refresh_minutes"), 60)),
                "cache_ttl_minutes": _safe_int(effective.get("cache_ttl_minutes"), _safe_int(source.get("default_cache_ttl_minutes"), 60)),
                "stale_after_minutes": _safe_int(source.get("stale_after_minutes"), 180),
            },
            "retrieval": {
                "last_attempt_at": runtime.get("last_attempt_at"),
                "last_success_at": runtime.get("last_success_at"),
                "last_status": runtime.get("last_status", "never_run"),
                "last_data_state": runtime.get("last_data_state", "unknown"),
                "last_record_count": _safe_int(runtime.get("last_record_count")),
                "age_minutes": health.get("age_minutes"),
                "freshness": health.get("freshness", "unknown"),
                "condition": health.get("state", "never_run"),
                "due": bool(health.get("due", False)),
            },
            "data_state": classification,
            "completeness": completeness,
            "schema": schema,
            "resilience": resilience,
            "quality": source.get("quality") or {},
            "public_note": source.get("public_note"),
        }

    @staticmethod
    def _summary(rows: list[Mapping[str, Any]]) -> dict[str, int]:
        summary = {name: 0 for name in CLASSIFICATIONS}
        summary.update({"stale_marked": 0, "metadata_complete": 0, "metadata_incomplete": 0, "schema_changed": 0, "schema_unobserved": 0, "circuit_open": 0})
        for row in rows:
            state = str((row.get("data_state") or {}).get("presentation") or "unavailable")
            summary[state] = summary.get(state, 0) + 1
            if (row.get("data_state") or {}).get("stale_marker_required"):
                summary["stale_marked"] += 1
            if (row.get("completeness") or {}).get("complete"):
                summary["metadata_complete"] += 1
            else:
                summary["metadata_incomplete"] += 1
            schema_state = str((row.get("schema") or {}).get("status"))
            if schema_state == "changed":
                summary["schema_changed"] += 1
            if schema_state == "not_observed":
                summary["schema_unobserved"] += 1
            if (row.get("resilience") or {}).get("circuit_breaker_state") == "open":
                summary["circuit_open"] += 1
        return summary

    def directory(self) -> dict[str, Any]:
        registry = self.operations.registry(public=True)
        rows = [self._row(source) for source in registry.get("sources", [])]
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "data-freshness-coverage-and-source-truth",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "application_mode": "demonstration" if self.settings.demo_mode else "production",
            "source_count": len(rows),
            "summary": self._summary(rows),
            "sources": rows,
            "classification_policy": {
                "allowed_states": list(CLASSIFICATIONS),
                "cached_is_live": False,
                "stale_is_live": False,
                "demonstration_is_live": False,
                "context_only_is_live": False,
                "missing_success_is_live": False,
            },
            "boundaries": [
                "Freshness describes retrieval time and declared thresholds; it does not certify source accuracy.",
                "Cached, historical, demonstration, and context-only records are never labeled live.",
                "Schema mismatches are review signals and do not authorize silent field substitution.",
                "Missing data remains visible and is not silently imputed.",
            ],
        }

    def source(self, feed_id: str) -> dict[str, Any]:
        key = str(feed_id or "").strip().lower().replace("-", "_")
        payload = self.directory()
        row = next((item for item in payload["sources"] if item["feed_id"] == key), None)
        if row is None:
            raise KeyError(key)
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "generated_at": payload["generated_at"],
            "source": row,
            "boundaries": payload["boundaries"],
        }


def public_data_truth(settings: Settings) -> dict[str, Any]:
    return DataTruthCenter(settings).directory()


def public_data_truth_source(settings: Settings, feed_id: str) -> dict[str, Any]:
    return DataTruthCenter(settings).source(feed_id)
