from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from ..api_reliability_v45531 import (
    api_contract_truth_manifest,
    build_capability_health,
    build_readiness,
    normalize_reliable_payload,
)
from ..config import Settings, get_settings
from ..economics_markets_sustainability import build_economic_records
from ..humanitarian_conflict_displacement_observatory import build_records as build_humanitarian_records
from ..international_law_observatory import build_law_records
from ..scientific_earth_systems_observatory import build_science_records
from ..trade_energy_resource_security_observatory import build_records as build_resource_records
from ..unified_country_regional_dossiers import build_country_dossier

router = APIRouter(tags=["api-reliability"])


def _respond(payload, capability: str):
    normalized, status = normalize_reliable_payload(payload, capability=capability)
    return JSONResponse(status_code=status, content=normalized)


@router.get("/ready")
def readiness(settings: Settings = Depends(get_settings)):
    payload = build_readiness(settings)
    return JSONResponse(status_code=200 if payload["ready"] else 503, content=payload)


@router.get("/public/api-contract-truth")
def api_contract_truth():
    return api_contract_truth_manifest()


@router.get("/public/capability-health")
def capability_health(
    probe: bool = Query(default=False),
    settings: Settings = Depends(get_settings),
):
    return build_capability_health(settings, probe=probe)


@router.get("/public/reliable/economics/records")
def reliable_economics_records(
    geography_code: str = Query(default=""),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_economic_records(settings, geography_code=geography_code, limit=limit), "economics")


@router.get("/public/reliable/law/records")
def reliable_law_records(
    country: str = Query(default=""),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_law_records(settings, country=country, limit=limit), "law")


@router.get("/public/reliable/science/records")
def reliable_science_records(
    geography_code: str = Query(default=""),
    query: str = Query(default=""),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_science_records(settings, geography_code=geography_code, query=query, limit=limit), "science")


@router.get("/public/reliable/humanitarian/records")
def reliable_humanitarian_records(
    country: str = Query(default=""),
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_humanitarian_records(settings, country=country, days=days, limit=limit), "humanitarian")


@router.get("/public/reliable/resources/records")
def reliable_resource_records(
    geography_code: str = Query(default=""),
    limit: int = Query(default=80, ge=1, le=300),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_resource_records(settings, geography_code=geography_code, limit=limit), "resources")


@router.get("/public/reliable/dossiers/country")
def reliable_country_dossier(
    country: str = Query(..., min_length=2, max_length=20),
    limit_per_domain: int = Query(default=12, ge=5, le=60),
    settings: Settings = Depends(get_settings),
):
    return _respond(build_country_dossier(settings, country=country, limit_per_domain=limit_per_domain), "dossiers")
