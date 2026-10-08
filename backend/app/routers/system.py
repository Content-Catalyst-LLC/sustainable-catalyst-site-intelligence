from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from ..build_info import (
    public_build_info as build_public_build_info,
    public_deployment_status as build_public_deployment_status,
)
from ..cartographic_interaction_v3232 import (
    public_map_interaction_contract as build_public_map_interaction_contract,
)
from ..config import Settings, get_settings
from ..deployment_gate_v3226 import build_release_gate
from ..deployment_receipt_v3226 import (
    public_deployment_receipt as build_public_deployment_receipt,
)
from ..ga4_client import GA4Client, get_ga4_client
from ..runtime_diagnostics_v3224 import build_runtime_health
from ..runtime_recovery_v3224 import build_runtime_recovery_contract

router = APIRouter(tags=["system"])


@router.get("/")
def root(settings: Settings = Depends(get_settings)):
    return {
        "ok": True,
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
def health(
    settings: Settings = Depends(get_settings),
    ga4: GA4Client = Depends(get_ga4_client),
):
    return {
        "ok": True,
        "alive": True,
        "state": "alive",
        "scope": "process-only",
        "dependency_readiness_asserted": False,
        "readiness_route": "/ready",
        "capability_health_route": "/public/capability-health",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "ga4_enabled": ga4.enabled,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/public/build-info")
def public_build_info():
    return build_public_build_info()


@router.get("/public/deployment-status")
def public_deployment_status():
    return build_public_deployment_status()


@router.get("/public/deployment-receipt")
def public_deployment_receipt():
    return build_public_deployment_receipt()


@router.get("/public/release-gate")
def public_release_gate(
    plugin_version: str | None = Query(default=None),
    expected_commit: str | None = Query(default=None),
    expected_release_id: str | None = Query(default=None),
):
    return build_release_gate(
        plugin_version=plugin_version,
        expected_commit=expected_commit,
        expected_release_id=expected_release_id,
    )


@router.get("/public/runtime-health")
def public_runtime_health(settings: Settings = Depends(get_settings)):
    return build_runtime_health(settings)


@router.get("/public/runtime-recovery")
def public_runtime_recovery(settings: Settings = Depends(get_settings)):
    return build_runtime_recovery_contract(settings)


@router.get("/public/maps/interaction")
def public_map_interaction():
    return build_public_map_interaction_contract()
