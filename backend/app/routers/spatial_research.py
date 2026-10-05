from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, HTTPException

from ..spatial_research_handoffs_v4510 import (
    build_package,
    compatibility_manifest,
    compose_research_object,
    create_handoff,
    handoff_registry,
    object_schema_manifest,
    registry_manifest,
    research_manifest,
    validate_handoff,
    validate_research_object,
)

router = APIRouter(tags=["Spatial Research"])


def _bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/public/spatial-research/registry")
def public_spatial_research_registry() -> dict[str, Any]:
    return registry_manifest()


@router.get("/public/spatial-research/object-schema")
def public_spatial_research_object_schema() -> dict[str, Any]:
    return object_schema_manifest()


@router.post("/public/spatial-research/objects/compose")
def public_spatial_research_compose(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return compose_research_object(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/spatial-research/objects/validate")
def public_spatial_research_validate(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return validate_research_object(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/spatial-research/objects/manifest")
def public_spatial_research_manifest(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return research_manifest(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/spatial-research/handoffs")
def public_spatial_research_handoffs() -> dict[str, Any]:
    return handoff_registry()


@router.post("/public/spatial-research/handoff/{target}")
def public_spatial_research_handoff(target: str, request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return create_handoff(target, request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/spatial-research/handoff/{target}/validate")
def public_spatial_research_handoff_validate(target: str, request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return validate_handoff(target, request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/spatial-research/package")
def public_spatial_research_package(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return build_package(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/spatial-research/compatibility")
def public_spatial_research_compatibility() -> dict[str, Any]:
    return compatibility_manifest()
