from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from ..api_reliability_v455311 import (
    api_contract_truth_manifest,
    build_capability_health,
    build_readiness,
    probe_capability,
)
from ..config import Settings, get_settings

router = APIRouter(tags=["api-reliability"])


def _respond(capability: str, settings: Settings, *, country: str = "KEN", limit: int = 80, query: str = ""):
    payload, status = probe_capability(capability, settings, country=country, limit=limit, query=query)
    return JSONResponse(status_code=status, content=payload)


@router.get("/ready")
def readiness(
    country: str = Query(default="KEN", min_length=2, max_length=80),
    settings: Settings = Depends(get_settings),
):
    payload = build_readiness(settings, country=country)
    return JSONResponse(status_code=200 if payload["ready"] else 503, content=payload)


@router.get("/public/api-contract-truth")
def api_contract_truth():
    return api_contract_truth_manifest()


@router.get("/public/capability-health")
def capability_health(
    probe: bool = Query(default=False),
    country: str = Query(default="KEN", min_length=2, max_length=80),
    settings: Settings = Depends(get_settings),
):
    return build_capability_health(settings, probe=probe, country=country)


@router.get("/public/reliable/economics/records")
def reliable_economics_records(
    geography_code: str = Query(default="KEN"),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond("economics", settings, country=geography_code, limit=limit)


@router.get("/public/reliable/law/records")
def reliable_law_records(
    country: str = Query(default="KEN"),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond("law", settings, country=country, limit=limit)


@router.get("/public/reliable/science/records")
def reliable_science_records(
    geography_code: str = Query(default="KEN"),
    query: str = Query(default=""),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond("science", settings, country=geography_code, query=query, limit=limit)


@router.get("/public/reliable/humanitarian/records")
def reliable_humanitarian_records(
    country: str = Query(default="KEN"),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond("humanitarian", settings, country=country, limit=limit)


@router.get("/public/reliable/resources/records")
def reliable_resource_records(
    geography_code: str = Query(default="KEN"),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond("resources", settings, country=geography_code, limit=limit)


@router.get("/public/reliable/dossiers/country")
def reliable_country_dossier(
    country: str = Query(..., min_length=2, max_length=80),
    limit_per_domain: int = Query(default=12, ge=5, le=60),
    settings: Settings = Depends(get_settings),
):
    return _respond("dossiers", settings, country=country, limit=limit_per_domain)
