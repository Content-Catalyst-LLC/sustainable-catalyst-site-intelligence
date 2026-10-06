from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, HTTPException
from ..scenario_exposure_change_v4530 import registry_manifest, schema_manifest, normalize_scenario, compare_scenarios, derive_change, evaluate_exposure, evaluate_thresholds, graph_context, live_context, prediction_context, research_context, compatibility_manifest
router = APIRouter(tags=["Scenario Exposure Change"])
def _call(fn, payload):
    try: return fn(payload)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
@router.get("/public/scenario-exposure/registry")
def registry(): return registry_manifest()
@router.get("/public/scenario-exposure/schema")
def schema(): return schema_manifest()
@router.post("/public/scenario-exposure/scenario/normalize")
def scenario_normalize(request: dict[str,Any]=Body(default={})): return _call(normalize_scenario, request)
@router.post("/public/scenario-exposure/scenario/compare")
def scenario_compare(request: dict[str,Any]=Body(default={})): return _call(compare_scenarios, request)
@router.post("/public/scenario-exposure/change/derive")
def change_derive(request: dict[str,Any]=Body(default={})): return _call(derive_change, request)
@router.post("/public/scenario-exposure/exposure/evaluate")
def exposure_evaluate(request: dict[str,Any]=Body(default={})): return _call(evaluate_exposure, request)
@router.post("/public/scenario-exposure/thresholds/evaluate")
def thresholds_evaluate(request: dict[str,Any]=Body(default={})): return _call(evaluate_thresholds, request)
@router.post("/public/scenario-exposure/graph/context")
def graph_ctx(request: dict[str,Any]=Body(default={})): return _call(graph_context, request)
@router.post("/public/scenario-exposure/live/context")
def live_ctx(request: dict[str,Any]=Body(default={})): return _call(live_context, request)
@router.post("/public/scenario-exposure/prediction/context")
def prediction_ctx(request: dict[str,Any]=Body(default={})): return _call(prediction_context, request)
@router.post("/public/scenario-exposure/research-context")
def research_ctx(request: dict[str,Any]=Body(default={})): return _call(research_context, request)
@router.get("/public/scenario-exposure/compatibility")
def compatibility(): return compatibility_manifest()
