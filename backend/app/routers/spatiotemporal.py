from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ..spatiotemporal_query_v4470 import (
    compatibility_contract,
    compile_query_plan,
    cross_layer_analysis,
    cross_layer_join,
    engine_manifest,
    execute_query,
    operator_manifest,
    query_schema_contract,
)

router = APIRouter(tags=["spatiotemporal-analysis"])


@router.get("/public/spatiotemporal/registry")
def public_spatiotemporal_registry():
    return engine_manifest()


@router.get("/public/spatiotemporal/query-schema")
def public_spatiotemporal_query_schema():
    return query_schema_contract()


@router.get("/public/spatiotemporal/operators")
def public_spatiotemporal_operators():
    return operator_manifest()


@router.post("/public/spatiotemporal/query/plan")
def public_spatiotemporal_query_plan(request: dict[str, Any] = Body(default={})):
    try:
        return compile_query_plan(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatiotemporal/query/execute")
def public_spatiotemporal_query_execute(request: dict[str, Any] = Body(default={})):
    try:
        return execute_query(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatiotemporal/cross-layer/join")
def public_spatiotemporal_cross_layer_join(request: dict[str, Any] = Body(default={})):
    try:
        return cross_layer_join(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatiotemporal/cross-layer/analyze")
def public_spatiotemporal_cross_layer_analyze(request: dict[str, Any] = Body(default={})):
    try:
        return cross_layer_analysis(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/public/spatiotemporal/compatibility")
def public_spatiotemporal_compatibility():
    return compatibility_contract()
