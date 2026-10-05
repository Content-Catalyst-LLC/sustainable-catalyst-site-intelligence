from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ..live_geospatial_event_fusion_v4490 import (
    build_snapshot,
    compatibility_contract,
    event_schema_contract,
    fuse_graph,
    fuse_layers,
    lifecycle_manifest,
    normalize_event,
    normalize_source_event,
    query_events,
    reconcile_events,
    registry_manifest,
    source_manifest,
    transition_event,
)

router = APIRouter(tags=["live-geospatial-event-fusion"])


@router.get("/public/live-geospatial/registry")
def public_live_geospatial_registry():
    return registry_manifest()


@router.get("/public/live-geospatial/event-schema")
def public_live_geospatial_event_schema():
    return event_schema_contract()


@router.get("/public/live-geospatial/sources")
def public_live_geospatial_sources():
    return source_manifest()


@router.get("/public/live-geospatial/lifecycle")
def public_live_geospatial_lifecycle():
    return lifecycle_manifest()


def _post(fn, request: dict[str, Any]):
    try:
        return fn(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/live-geospatial/events/normalize")
def public_live_geospatial_normalize(request: dict[str, Any] = Body(default={})):
    return _post(normalize_event, request)


@router.post("/public/live-geospatial/events/normalize-source")
def public_live_geospatial_normalize_source(request: dict[str, Any] = Body(default={})):
    return _post(normalize_source_event, request)


@router.post("/public/live-geospatial/events/reconcile")
def public_live_geospatial_reconcile(request: dict[str, Any] = Body(default={})):
    return _post(reconcile_events, request)


@router.post("/public/live-geospatial/events/query")
def public_live_geospatial_query(request: dict[str, Any] = Body(default={})):
    return _post(query_events, request)


@router.post("/public/live-geospatial/lifecycle/transition")
def public_live_geospatial_transition(request: dict[str, Any] = Body(default={})):
    return _post(transition_event, request)


@router.post("/public/live-geospatial/fuse/layers")
def public_live_geospatial_fuse_layers(request: dict[str, Any] = Body(default={})):
    return _post(fuse_layers, request)


@router.post("/public/live-geospatial/fuse/graph")
def public_live_geospatial_fuse_graph(request: dict[str, Any] = Body(default={})):
    return _post(fuse_graph, request)


@router.post("/public/live-geospatial/snapshot")
def public_live_geospatial_snapshot(request: dict[str, Any] = Body(default={})):
    return _post(build_snapshot, request)


@router.get("/public/live-geospatial/compatibility")
def public_live_geospatial_compatibility():
    return compatibility_contract()
