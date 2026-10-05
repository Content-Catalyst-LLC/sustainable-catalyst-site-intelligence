from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, HTTPException, Query

from ..global_source_federation_v4500 import (
    authority_types_manifest,
    compatibility_manifest,
    evaluate_trust_profile,
    federation_plan,
    jurisdiction_manifest,
    regions_manifest,
    registry_manifest,
    select_source,
    source_detail,
    source_manifest,
)

router = APIRouter(tags=["Source Federation"])


def _bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/public/source-federation/registry")
def public_source_federation_registry() -> dict[str, Any]:
    return registry_manifest()


@router.get("/public/source-federation/authorities")
def public_source_federation_authorities(
    jurisdiction: str = Query(default=""),
    region: str = Query(default=""),
    domain: str = Query(default=""),
    language: str = Query(default=""),
    authority_class: str = Query(default=""),
    federation_mode: str = Query(default=""),
    query: str = Query(default=""),
) -> dict[str, Any]:
    return source_manifest(jurisdiction=jurisdiction, region=region, domain=domain, language=language, authority_class=authority_class, federation_mode=federation_mode, query=query)


@router.get("/public/source-federation/authorities/{source_id}")
def public_source_federation_authority(source_id: str) -> dict[str, Any]:
    try:
        return source_detail(source_id)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/source-federation/regions")
def public_source_federation_regions() -> dict[str, Any]:
    return regions_manifest()


@router.get("/public/source-federation/jurisdictions/{code}")
def public_source_federation_jurisdiction(code: str) -> dict[str, Any]:
    try:
        return jurisdiction_manifest(code)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/source-federation/authority-types")
def public_source_federation_authority_types() -> dict[str, Any]:
    return authority_types_manifest()


@router.post("/public/source-federation/select")
def public_source_federation_select(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return select_source(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/source-federation/federate")
def public_source_federation_plan(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return federation_plan(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/source-federation/trust-profile/evaluate")
def public_source_federation_trust_evaluate(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return evaluate_trust_profile(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/source-federation/compatibility")
def public_source_federation_compatibility() -> dict[str, Any]:
    return compatibility_manifest()
