from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, HTTPException
from ..reproducible_spatial_packages_v4540 import (
    registry_manifest, schema_manifest, profiles_manifest, compose_package, verify_package,
    inspect_package, build_manifest, reproduction_plan, export_plan, compare_packages,
    research_context, compatibility_manifest,
)
router = APIRouter(tags=["Reproducible Spatial Intelligence Packages"])
def _call(fn, payload):
    try: return fn(payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
@router.get("/public/reproducible-spatial-packages/registry")
def registry(): return registry_manifest()
@router.get("/public/reproducible-spatial-packages/schema")
def schema(): return schema_manifest()
@router.get("/public/reproducible-spatial-packages/profiles")
def profiles(): return profiles_manifest()
@router.post("/public/reproducible-spatial-packages/compose")
def compose(request: dict[str,Any]=Body(default={})): return _call(compose_package, request)
@router.post("/public/reproducible-spatial-packages/verify")
def verify(request: dict[str,Any]=Body(default={})): return _call(verify_package, request)
@router.post("/public/reproducible-spatial-packages/inspect")
def inspect(request: dict[str,Any]=Body(default={})): return _call(inspect_package, request)
@router.post("/public/reproducible-spatial-packages/manifest")
def manifest(request: dict[str,Any]=Body(default={})): return _call(build_manifest, request)
@router.post("/public/reproducible-spatial-packages/reproduction-plan")
def reproduction(request: dict[str,Any]=Body(default={})): return _call(reproduction_plan, request)
@router.post("/public/reproducible-spatial-packages/export-plan")
def export(request: dict[str,Any]=Body(default={})): return _call(export_plan, request)
@router.post("/public/reproducible-spatial-packages/compare")
def compare(request: dict[str,Any]=Body(default={})): return _call(compare_packages, request)
@router.post("/public/reproducible-spatial-packages/research-context")
def research(request: dict[str,Any]=Body(default={})): return _call(research_context, request)
@router.get("/public/reproducible-spatial-packages/compatibility")
def compatibility(): return compatibility_manifest()
