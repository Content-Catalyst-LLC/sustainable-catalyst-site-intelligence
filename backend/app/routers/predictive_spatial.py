from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, HTTPException

from ..predictive_spatial_consumer_v4520 import (
    bind_prediction,
    calibration_context,
    compare_predictions,
    compatibility_manifest,
    normalize_prediction,
    provider_manifest,
    query_predictions,
    registry_manifest,
    research_context,
    scenario_context,
    schema_manifest,
    validate_prediction,
)

router = APIRouter(tags=["Predictive Spatial Intelligence"])


def _bad(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/public/predictive-spatial/registry")
def public_predictive_spatial_registry() -> dict[str, Any]:
    return registry_manifest()


@router.get("/public/predictive-spatial/schema")
def public_predictive_spatial_schema() -> dict[str, Any]:
    return schema_manifest()


@router.get("/public/predictive-spatial/providers")
def public_predictive_spatial_providers() -> dict[str, Any]:
    return provider_manifest()


@router.post("/public/predictive-spatial/normalize")
def public_predictive_spatial_normalize(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return normalize_prediction(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/validate")
def public_predictive_spatial_validate(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return validate_prediction(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/bind")
def public_predictive_spatial_bind(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return bind_prediction(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/query")
def public_predictive_spatial_query(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return query_predictions(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/compare")
def public_predictive_spatial_compare(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return compare_predictions(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/scenario")
def public_predictive_spatial_scenario(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return scenario_context(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/calibration")
def public_predictive_spatial_calibration(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return calibration_context(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.post("/public/predictive-spatial/research-context")
def public_predictive_spatial_research_context(request: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    try:
        return research_context(request)
    except ValueError as exc:
        raise _bad(exc) from exc


@router.get("/public/predictive-spatial/compatibility")
def public_predictive_spatial_compatibility() -> dict[str, Any]:
    return compatibility_manifest()
