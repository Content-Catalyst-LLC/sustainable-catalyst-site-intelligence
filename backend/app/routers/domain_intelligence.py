from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, HTTPException

from ..advanced_domain_intelligence_v4552 import (
    registry_manifest,
    domain_profile,
    analyze,
    research_packet,
    parity_audit,
    compatibility_manifest,
)

router = APIRouter(tags=["Advanced Domain Intelligence"])


def _call(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/public/domain-intelligence/registry")
def registry(): return registry_manifest()

@router.get("/public/domain-intelligence/parity-audit")
def parity(): return parity_audit()

@router.get("/public/domain-intelligence/compatibility")
def compatibility(): return compatibility_manifest()


def _profile(domain: str): return _call(domain_profile, domain)
def _analyze(domain: str, request: dict[str, Any]): return _call(analyze, domain, request)
def _packet(domain: str, request: dict[str, Any]): return _call(research_packet, domain, request)

@router.get("/public/domain-intelligence/dossiers/profile")
def dossiers_profile(): return _profile("dossiers")
@router.post("/public/domain-intelligence/dossiers/analyze")
def dossiers_analyze(request: dict[str, Any] = Body(default={})): return _analyze("dossiers", request)
@router.post("/public/domain-intelligence/dossiers/packet")
def dossiers_packet(request: dict[str, Any] = Body(default={})): return _packet("dossiers", request)

@router.get("/public/domain-intelligence/economics/profile")
def economics_profile(): return _profile("economics")
@router.post("/public/domain-intelligence/economics/analyze")
def economics_analyze(request: dict[str, Any] = Body(default={})): return _analyze("economics", request)
@router.post("/public/domain-intelligence/economics/packet")
def economics_packet(request: dict[str, Any] = Body(default={})): return _packet("economics", request)

@router.get("/public/domain-intelligence/international-law/profile")
def law_profile(): return _profile("international-law")
@router.post("/public/domain-intelligence/international-law/analyze")
def law_analyze(request: dict[str, Any] = Body(default={})): return _analyze("international-law", request)
@router.post("/public/domain-intelligence/international-law/packet")
def law_packet(request: dict[str, Any] = Body(default={})): return _packet("international-law", request)

@router.get("/public/domain-intelligence/science/profile")
def science_profile(): return _profile("science")
@router.post("/public/domain-intelligence/science/analyze")
def science_analyze(request: dict[str, Any] = Body(default={})): return _analyze("science", request)
@router.post("/public/domain-intelligence/science/packet")
def science_packet(request: dict[str, Any] = Body(default={})): return _packet("science", request)

@router.get("/public/domain-intelligence/humanitarian/profile")
def humanitarian_profile(): return _profile("humanitarian")
@router.post("/public/domain-intelligence/humanitarian/analyze")
def humanitarian_analyze(request: dict[str, Any] = Body(default={})): return _analyze("humanitarian", request)
@router.post("/public/domain-intelligence/humanitarian/packet")
def humanitarian_packet(request: dict[str, Any] = Body(default={})): return _packet("humanitarian", request)

@router.get("/public/domain-intelligence/resources/profile")
def resources_profile(): return _profile("resources")
@router.post("/public/domain-intelligence/resources/analyze")
def resources_analyze(request: dict[str, Any] = Body(default={})): return _analyze("resources", request)
@router.post("/public/domain-intelligence/resources/packet")
def resources_packet(request: dict[str, Any] = Body(default={})): return _packet("resources", request)
