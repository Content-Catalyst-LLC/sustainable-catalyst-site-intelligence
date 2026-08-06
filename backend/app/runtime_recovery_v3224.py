"""Public-safe recovery contract for Site Intelligence v3.23.4.

This module describes the browser recovery policy without performing outbound
network calls. The client runtime applies bounded retries, per-service circuit
breakers, and last-known-good public JSON fallbacks while keeping failures
isolated to the affected service group.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import Settings
from .version import APP_VERSION

RECOVERABLE_STATUS_CODES = (408, 425, 429, 500, 502, 503, 504)

SERVICE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "core",
        "label": "Core application",
        "path_prefixes": ("/health", "/public/build-info", "/public/runtime-"),
        "critical": True,
        "stale_ttl_seconds": 900,
    },
    {
        "id": "geospatial",
        "label": "Maps and spatial evidence",
        "path_prefixes": ("/public/geospatial", "/public/spatial", "/public/earth", "/public/events"),
        "critical": True,
        "stale_ttl_seconds": 21600,
    },
    {
        "id": "country",
        "label": "Country and comparative intelligence",
        "path_prefixes": ("/public/country", "/public/global-country", "/public/compare", "/public/dossiers"),
        "critical": False,
        "stale_ttl_seconds": 21600,
    },
    {
        "id": "indicators",
        "label": "Indicators and thematic intelligence",
        "path_prefixes": (
            "/public/global-conditions",
            "/public/economics",
            "/public/science",
            "/public/humanitarian",
            "/public/resources",
            "/public/thematic",
        ),
        "critical": False,
        "stale_ttl_seconds": 21600,
    },
    {
        "id": "research",
        "label": "Research, evidence, and publishing",
        "path_prefixes": (
            "/public/research",
            "/public/evidence",
            "/public/knowledge-graph",
            "/public/intelligence-publishing",
            "/public/source-methodology",
        ),
        "critical": False,
        "stale_ttl_seconds": 86400,
    },
    {
        "id": "operations",
        "label": "Monitoring and platform operations",
        "path_prefixes": (
            "/public/monitoring",
            "/public/workspaces",
            "/public/workflows",
            "/public/federation",
            "/public/production-governance",
            "/public/platform",
        ),
        "critical": False,
        "stale_ttl_seconds": 3600,
    },
)


def build_runtime_recovery_contract(settings: Settings) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ready",
        "version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "public-client-recovery-contract",
        "live_upstream_checks_performed": False,
        "client_asset": "/app/assets/service-recovery-v3224.js",
        "policy": {
            "eligible_requests": "same-origin GET requests for public JSON resources",
            "maximum_attempts": 3,
            "request_timeout_ms": 12000,
            "retry_backoff_ms": [600, 1400],
            "recoverable_status_codes": list(RECOVERABLE_STATUS_CODES),
            "circuit_failure_threshold": 3,
            "circuit_cooldown_ms": 30000,
            "automatic_probe_interval_ms": 30000,
            "cache_scope": "public JSON only",
            "cache_storage": "browser Cache API with in-memory fallback",
            "default_stale_ttl_seconds": 21600,
        },
        "service_groups": [
            {
                **group,
                "path_prefixes": list(group["path_prefixes"]),
                "recovery": "bounded retry → circuit isolation → last-known-good response → automatic probe",
            }
            for group in SERVICE_GROUPS
        ],
        "protections": [
            "Mutation requests are never retried or cached.",
            "Cross-origin requests are never intercepted.",
            "Runtime diagnostic probes bypass cached recovery responses.",
            "A circuit opens only for its affected service group.",
            "Recovered service groups emit a browser event so the active workspace can refresh once.",
            "Cached public JSON is marked with recovery headers and an explicit stale age.",
        ],
        "embed_policy": {
            "public_embeds_enabled": bool(settings.public_embeds_enabled),
            "same_origin_recovery_only": True,
        },
        "limitations": [
            "Recovery cannot manufacture data that has never loaded successfully in the browser.",
            "Last-known-good responses may be stale and are reported as recovered cache responses.",
            "Third-party map tile recovery is handled by the separate first-party map reliability runtime.",
        ],
    }
