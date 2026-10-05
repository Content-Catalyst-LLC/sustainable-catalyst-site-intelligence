from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..data_truth_control_plane_v3240 import (
    public_control_plane as build_public_control_plane,
    public_control_plane_coverage as build_public_control_plane_coverage,
    public_control_plane_export as build_public_control_plane_export,
    public_control_plane_history as build_public_control_plane_history,
    public_control_plane_outages as build_public_control_plane_outages,
    public_control_plane_schema_drift as build_public_control_plane_schema_drift,
    public_control_plane_source as build_public_control_plane_source,
    public_control_plane_sources as build_public_control_plane_sources,
    public_control_plane_workspaces as build_public_control_plane_workspaces,
)
from ..data_truth_v32371 import (
    public_country_data_truth as build_public_country_data_truth,
    public_country_indicator_truth as build_public_country_indicator_truth,
    public_country_source_truth as build_public_country_source_truth,
    public_coverage_matrix as build_public_coverage_matrix,
    public_data_truth as build_public_data_truth,
    public_data_truth_countries as build_public_data_truth_countries,
    public_data_truth_source as build_public_data_truth_source,
)
from ..record_provenance_v4358 import (
    public_country_record_truth as build_public_country_record_truth,
    public_indicator_record_truth as build_public_indicator_record_truth,
    public_map_layer_truth as build_public_map_layer_truth,
    public_normalized_record_truth as build_public_normalized_record_truth,
    public_record_truth_manifest as build_public_record_truth_manifest,
)
from ..workspace_evidence_unification_v4358 import (
    canonical_country_indicator as build_canonical_country_indicator,
    canonical_country_observations as build_canonical_country_observations,
    overview as build_workspace_evidence_overview,
    readiness as build_workspace_evidence_readiness,
)

router = APIRouter(tags=["data-truth"])


@router.get("/public/data-truth")
def public_data_truth_endpoint(
    country: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_data_truth(settings, country_code=country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/public/data-truth/countries")
def public_data_truth_countries_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_data_truth_countries(settings)


@router.get("/public/data-truth/coverage-matrix")
def public_data_truth_coverage_matrix_endpoint(
    countries: str = Query(default=""),
    region: str = Query(default=""),
    source: str = Query(default=""),
    state: str = Query(default=""),
    limit: int = Query(default=24, ge=1, le=60),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    return build_public_coverage_matrix(
        settings,
        countries=country_codes,
        region=region,
        source_id=source,
        state=state,
        limit=limit,
        offset=offset,
    )


@router.get("/public/data-truth/country/{country_code}")
def public_country_data_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_data_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/data-truth/country/{country_code}/sources")
def public_country_source_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_source_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/data-truth/country/{country_code}/indicators")
def public_country_indicator_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_indicator_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/data-truth/control-plane")
def public_data_truth_control_plane_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane(settings)


@router.get("/public/data-truth/control-plane/sources")
def public_data_truth_control_plane_sources_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_sources(settings)


@router.get("/public/data-truth/control-plane/source/{feed_id}")
def public_data_truth_control_plane_source_endpoint(feed_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_control_plane_source(settings, feed_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc


@router.get("/public/data-truth/control-plane/history")
def public_data_truth_control_plane_history_endpoint(
    source: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_control_plane_history(settings, source, limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc


@router.get("/public/data-truth/control-plane/schema-drift")
def public_data_truth_control_plane_schema_drift_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_schema_drift(settings)


@router.get("/public/data-truth/control-plane/outages")
def public_data_truth_control_plane_outages_endpoint(settings: Settings = Depends(get_settings)):
    return build_public_control_plane_outages(settings)


@router.get("/public/data-truth/control-plane/coverage")
def public_data_truth_control_plane_coverage_endpoint(
    countries: str = Query(default=""),
    settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    return build_public_control_plane_coverage(settings, country_codes)


@router.get("/public/data-truth/control-plane/workspaces")
def public_data_truth_control_plane_workspaces_endpoint(
    country: str = Query(default="KEN"),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_control_plane_workspaces(settings, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/data-truth/control-plane/export")
def public_data_truth_control_plane_export_endpoint(
    countries: str = Query(default=""),
    country: str = Query(default="KEN"),
    settings: Settings = Depends(get_settings),
):
    country_codes = [item.strip().upper() for item in countries.split(",") if item.strip()] or None
    try:
        return build_public_control_plane_export(settings, country_codes, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country or source not found.") from exc


@router.get("/public/data-truth/{feed_id}")
def public_data_truth_source_endpoint(feed_id: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_data_truth_source(settings, feed_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data source not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/public/workspace-evidence")
def public_workspace_evidence_endpoint():
    return build_workspace_evidence_overview()


@router.get("/public/workspace-evidence/readiness")
def public_workspace_evidence_readiness_endpoint():
    return build_workspace_evidence_readiness()


@router.get("/public/workspace-evidence/country/{country_code}")
def public_workspace_evidence_country_endpoint(country_code: str):
    try:
        return build_canonical_country_observations(country_code)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/workspace-evidence/country/{country_code}/indicator/{indicator_id}")
def public_workspace_evidence_indicator_endpoint(country_code: str, indicator_id: str):
    try:
        return build_canonical_country_indicator(country_code, indicator_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Country or indicator not found.") from exc


@router.get("/public/record-truth/country/{country_code}")
def public_country_record_truth_endpoint(country_code: str, settings: Settings = Depends(get_settings)):
    try:
        return build_public_country_record_truth(settings, country_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc


@router.get("/public/record-truth/indicator/{country_code}/{indicator_id}")
def public_indicator_record_truth_endpoint(
    country_code: str,
    indicator_id: str,
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_indicator_record_truth(settings, country_code, indicator_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country or indicator not found.") from exc


@router.get("/public/record-truth/map-layer/{layer_id}")
def public_map_layer_truth_endpoint(
    layer_id: str,
    date: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_map_layer_truth(settings, layer_id, date=date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Map layer not found.") from exc


@router.post("/public/record-truth/resolve")
def public_normalized_record_truth_endpoint(
    record: dict[str, Any] = Body(...),
    settings: Settings = Depends(get_settings),
):
    return build_public_normalized_record_truth(settings, record)


@router.get("/public/record-truth/manifest")
def public_record_truth_manifest_endpoint(
    country: str = Query(default="KEN"),
    settings: Settings = Depends(get_settings),
):
    try:
        return build_public_record_truth_manifest(settings, country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found.") from exc
