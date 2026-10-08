from fastapi import APIRouter
from ..standalone_functional_parity_v45532 import manifest, routes, certification
router=APIRouter(prefix="/public/web-app/parity", tags=["Standalone Functional Parity"] )
@router.get("")
def get_manifest(): return manifest()
@router.get("/routes")
def get_routes(): return routes()
@router.get("/certification")
def get_certification(): return certification()
