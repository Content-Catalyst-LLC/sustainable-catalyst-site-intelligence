from __future__ import annotations

from fastapi import APIRouter

from ..standalone_web_application_v4553 import (
    manifest,
    route_manifest,
    config_manifest,
    context_contract,
    wordpress_decoupling_contract,
    compatibility_manifest,
)

router = APIRouter(tags=["standalone-web-application"])

@router.get("/public/web-app/manifest")
def web_app_manifest(): return manifest()

@router.get("/public/web-app/routes")
def web_app_routes(): return route_manifest()

@router.get("/public/web-app/config")
def web_app_config(): return config_manifest()

@router.get("/public/web-app/context")
def web_app_context(): return context_contract()

@router.get("/public/web-app/wordpress-decoupling")
def web_app_wordpress_decoupling(): return wordpress_decoupling_contract()

@router.get("/public/web-app/compatibility")
def web_app_compatibility(): return compatibility_manifest()
