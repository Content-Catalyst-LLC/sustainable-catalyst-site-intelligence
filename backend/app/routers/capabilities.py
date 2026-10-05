from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from ..route_registry_v4430 import capability_detail, capability_manifest, route_inventory
from ..version import APP_VERSION

router = APIRouter(tags=["capability-registry"])


@router.get("/public/capabilities")
def public_capabilities(request: Request):
    return capability_manifest(request.app.routes)


@router.get("/public/capabilities/{capability_id}")
def public_capability(capability_id: str, request: Request):
    payload = capability_detail(request.app.routes, capability_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Capability not found.")
    return payload


@router.get("/public/routes/registry")
def public_route_registry(
    request: Request,
    capability: str | None = Query(default=None),
    prefix: str | None = Query(default=None),
    modularized: bool | None = Query(default=None),
    limit: int = Query(default=250, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
):
    items = route_inventory(request.app.routes)
    if capability:
        items = [item for item in items if item["capability_id"] == capability]
    if prefix:
        items = [item for item in items if item["path"].startswith(prefix)]
    if modularized is not None:
        items = [item for item in items if item["modularized"] is modularized]
    total = len(items)
    page = items[offset:offset + limit]
    return {
        "ok": True,
        "version": APP_VERSION,
        "registry_version": "1.1.0",
        "total": total,
        "offset": offset,
        "limit": limit,
        "routes": page,
    }


@router.get("/public/routes/summary")
def public_route_summary(request: Request):
    manifest = capability_manifest(request.app.routes)
    return {
        "ok": True,
        "version": APP_VERSION,
        "registry_version": manifest["registry_version"],
        "route_count": manifest["route_count"],
        "modularized_route_count": manifest["modularized_route_count"],
        "legacy_main_route_count": manifest["legacy_main_route_count"],
        "unclassified_route_count": manifest["unclassified_route_count"],
        "capabilities": [
            {
                "capability_id": item["capability_id"],
                "route_count": item["route_count"],
                "modularized_route_count": item["modularized_route_count"],
            }
            for item in manifest["capabilities"]
        ],
    }
