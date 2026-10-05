from __future__ import annotations

from fastapi import APIRouter, Request

from ..wordpress_bridge_v4450 import (
    auth_handoff_contract,
    bridge_contract,
    compatibility_contract,
    embed_contract,
)

router = APIRouter(tags=["wordpress-integration"])


@router.get("/public/integrations/wordpress/bridge")
def wordpress_bridge(request: Request):
    return bridge_contract(request.app.routes)


@router.get("/public/integrations/wordpress/embed-contract")
def wordpress_embed_contract():
    return embed_contract()


@router.get("/public/integrations/wordpress/auth-handoff")
def wordpress_auth_handoff():
    return auth_handoff_contract()


@router.get("/public/integrations/wordpress/compatibility")
def wordpress_compatibility():
    return compatibility_contract()
