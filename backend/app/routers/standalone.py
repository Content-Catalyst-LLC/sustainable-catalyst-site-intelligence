from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from ..standalone_authority_v4440 import (
    build_bootstrap,
    navigation_model,
    runtime_handshake,
    session_contract,
)

router = APIRouter(tags=["standalone-application"])
PUBLIC_APP_DIR = Path(__file__).resolve().parents[2] / "public_app"


@router.get("/public/app/bootstrap")
def public_app_bootstrap(request: Request, surface: str | None = Query(default=None)):
    return build_bootstrap(request.app.routes, surface)


@router.get("/public/app/runtime-handshake")
def public_app_runtime_handshake(
    request: Request,
    client_version: str | None = Query(default=None),
    surface: str | None = Query(default=None),
):
    return runtime_handshake(request.app.routes, client_version, surface)


@router.get("/public/app/navigation")
def public_app_navigation(request: Request):
    return navigation_model(request.app.routes)


@router.get("/public/app/session-contract")
def public_app_session_contract():
    return session_contract()


@router.get("/app/manifest.webmanifest", include_in_schema=False)
def standalone_manifest():
    return FileResponse(str(PUBLIC_APP_DIR / "manifest.webmanifest"), media_type="application/manifest+json")


@router.get("/app/service-worker.js", include_in_schema=False)
def standalone_service_worker():
    return FileResponse(str(PUBLIC_APP_DIR / "service-worker.js"), media_type="application/javascript")


@router.get("/app/offline.html", include_in_schema=False)
def standalone_offline_page():
    return FileResponse(str(PUBLIC_APP_DIR / "offline.html"), media_type="text/html")


@router.get("/app", include_in_schema=False)
@router.get("/app/", include_in_schema=False)
@router.get("/app/{route:path}", include_in_schema=False)
def standalone_public_app(route: str = ""):
    return FileResponse(str(PUBLIC_APP_DIR / "index.html"))
