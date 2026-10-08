from __future__ import annotations

from fastapi import APIRouter

from ..production_consolidation_v4560 import checklist, manifest, release_snapshot

router = APIRouter(prefix="/public/production-certification", tags=["Production Certification"])


@router.get("")
def production_certification_manifest():
    return manifest()


@router.get("/checklist")
def production_certification_checklist():
    return checklist()


@router.get("/release")
def production_certification_release():
    return release_snapshot()
