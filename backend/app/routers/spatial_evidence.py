from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from ..spatial_evidence_registry_v4460 import (
    compatibility_contract,
    domain_manifest,
    layer_detail,
    list_layers,
    normalize_evidence_object,
    object_schema_contract,
    registry_manifest,
    validate_evidence_object,
)

router = APIRouter(tags=["spatial-evidence-registry"])


@router.get("/public/spatial-evidence/registry")
def public_spatial_evidence_registry():
    return registry_manifest()


@router.get("/public/spatial-evidence/layers")
def public_spatial_evidence_layers(
    domain: str | None = Query(default=None),
    capability_id: str | None = Query(default=None),
    geometry_type: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=160),
):
    return list_layers(domain=domain, capability_id=capability_id, geometry_type=geometry_type, q=q)


@router.get("/public/spatial-evidence/layers/{layer_id}")
def public_spatial_evidence_layer(layer_id: str):
    payload=layer_detail(layer_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Spatial layer not found")
    return payload


@router.get("/public/spatial-evidence/domains")
def public_spatial_evidence_domains():
    return domain_manifest()


@router.get("/public/spatial-evidence/object-schema")
def public_spatial_evidence_object_schema():
    return object_schema_contract()


@router.post("/public/spatial-evidence/objects/normalize")
def public_spatial_evidence_normalize(request: dict[str, Any] = Body(default={})):
    try:
        return {"ok":True,"object":normalize_evidence_object(request)}
    except (TypeError,ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/public/spatial-evidence/objects/validate")
def public_spatial_evidence_validate(request: dict[str, Any] = Body(default={})):
    return validate_evidence_object(request)


@router.get("/public/spatial-evidence/compatibility")
def public_spatial_evidence_compatibility():
    return compatibility_contract()
