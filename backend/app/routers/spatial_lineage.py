from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, HTTPException
from ..spatial_provenance_lineage_v4550 import (
    registry_manifest, schema_manifest, transformation_types_manifest, record_transformation,
    validate_transformation, build_lineage_chain, lineage_graph, trace_lineage,
    verify_lineage_chain, package_context, compare_lineages, compatibility_manifest,
)
router = APIRouter(tags=["Spatial Provenance & Transformation Lineage"])
def _call(fn, payload):
    try: return fn(payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
@router.get("/public/spatial-lineage/registry")
def registry(): return registry_manifest()
@router.get("/public/spatial-lineage/schema")
def schema(): return schema_manifest()
@router.get("/public/spatial-lineage/transformation-types")
def types(): return transformation_types_manifest()
@router.post("/public/spatial-lineage/record")
def record(request: dict[str,Any]=Body(default={})): return _call(record_transformation, request)
@router.post("/public/spatial-lineage/validate")
def validate(request: dict[str,Any]=Body(default={})): return _call(validate_transformation, request)
@router.post("/public/spatial-lineage/chain")
def chain(request: dict[str,Any]=Body(default={})): return _call(build_lineage_chain, request)
@router.post("/public/spatial-lineage/graph")
def graph(request: dict[str,Any]=Body(default={})): return _call(lineage_graph, request)
@router.post("/public/spatial-lineage/trace")
def trace(request: dict[str,Any]=Body(default={})): return _call(trace_lineage, request)
@router.post("/public/spatial-lineage/verify")
def verify(request: dict[str,Any]=Body(default={})): return _call(verify_lineage_chain, request)
@router.post("/public/spatial-lineage/package-context")
def package(request: dict[str,Any]=Body(default={})): return _call(package_context, request)
@router.post("/public/spatial-lineage/compare")
def compare(request: dict[str,Any]=Body(default={})): return _call(compare_lineages, request)
@router.get("/public/spatial-lineage/compatibility")
def compatibility(): return compatibility_manifest()
