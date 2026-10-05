from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ..spatial_relationship_graph_v4480 import (
    analyze_graph,
    build_graph,
    compatibility_contract,
    graph_manifest,
    graph_neighborhood,
    graph_path,
    graph_schema_contract,
    query_graph,
    relationship_manifest,
)

router = APIRouter(tags=["spatial-relationship-graph"])


@router.get("/public/spatial-graph/registry")
def public_spatial_graph_registry():
    return graph_manifest()


@router.get("/public/spatial-graph/schema")
def public_spatial_graph_schema():
    return graph_schema_contract()


@router.get("/public/spatial-graph/relationship-types")
def public_spatial_graph_relationship_types():
    return relationship_manifest()


@router.post("/public/spatial-graph/build")
def public_spatial_graph_build(request: dict[str, Any] = Body(default={})):
    try:
        return build_graph(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatial-graph/query")
def public_spatial_graph_query(request: dict[str, Any] = Body(default={})):
    try:
        return query_graph(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatial-graph/neighborhood")
def public_spatial_graph_neighborhood(request: dict[str, Any] = Body(default={})):
    try:
        return graph_neighborhood(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatial-graph/path")
def public_spatial_graph_path(request: dict[str, Any] = Body(default={})):
    try:
        return graph_path(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatial-graph/analyze")
def public_spatial_graph_analyze(request: dict[str, Any] = Body(default={})):
    try:
        return analyze_graph(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/public/spatial-graph/compatibility")
def public_spatial_graph_compatibility():
    return compatibility_contract()
