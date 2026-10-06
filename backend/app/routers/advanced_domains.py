from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, HTTPException
from ..advanced_domain_workspaces_v4530 import registry_manifest, domain_profile, law_analysis, economics_analysis, ocean_analysis, space_analysis, parity_audit, research_context, compatibility_manifest
router=APIRouter(tags=["Advanced Domain Workspaces"])
def _call(fn,*args):
    try:return fn(*args)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
@router.get("/public/advanced-workspaces/registry")
def registry():return registry_manifest()
@router.get("/public/advanced-workspaces/international-law")
def law_profile():return _call(domain_profile,"international-law")
@router.post("/public/advanced-workspaces/international-law/analyze")
def law_analyze(request:dict[str,Any]=Body(default={})):return _call(law_analysis,request)
@router.get("/public/advanced-workspaces/economics")
def economics_profile():return _call(domain_profile,"economics")
@router.post("/public/advanced-workspaces/economics/analyze")
def economics_analyze(request:dict[str,Any]=Body(default={})):return _call(economics_analysis,request)
@router.get("/public/advanced-workspaces/ocean")
def ocean_profile():return _call(domain_profile,"ocean")
@router.post("/public/advanced-workspaces/ocean/analyze")
def ocean_analyze(request:dict[str,Any]=Body(default={})):return _call(ocean_analysis,request)
@router.get("/public/advanced-workspaces/space")
def space_profile():return _call(domain_profile,"space")
@router.post("/public/advanced-workspaces/space/analyze")
def space_analyze(request:dict[str,Any]=Body(default={})):return _call(space_analysis,request)
@router.get("/public/advanced-workspaces/parity-audit")
def parity():return parity_audit()
@router.post("/public/advanced-workspaces/research-context")
def research(request:dict[str,Any]=Body(default={})):return _call(research_context,request)
@router.get("/public/advanced-workspaces/compatibility")
def compatibility():return compatibility_manifest()
