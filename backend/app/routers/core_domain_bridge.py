from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..core_domain_bridge_v4561 import bridge_manifest, diagnostics, domain_coverage, source_catalog

router = APIRouter(prefix="/public/core-domain-bridge", tags=["core-domain-bridge"])


@router.get("")
def manifest(settings: Settings = Depends(get_settings)):
    return bridge_manifest(settings)


@router.get("/sources")
def sources(settings: Settings = Depends(get_settings)):
    return source_catalog(settings)


@router.get("/domains/{domain}")
def domain_sources(domain: str, settings: Settings = Depends(get_settings)):
    try:
        return domain_coverage(settings, domain=domain)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown Site Intelligence domain workspace.") from exc


@router.get("/diagnostics")
def bridge_diagnostics(
    probe: bool = Query(default=False),
    country: str = Query(default="KEN", min_length=2, max_length=80),
    settings: Settings = Depends(get_settings),
):
    return diagnostics(settings, probe=probe, country=country)
