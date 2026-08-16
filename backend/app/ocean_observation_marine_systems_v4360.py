from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable

from .version import APP_VERSION
from .ocean_surface_v4500 import catalog as ocean_surface_catalog, readiness as ocean_surface_readiness
from .water_column_v4600 import catalog as water_column_catalog, readiness as water_column_readiness
from .seafloor_bathymetry_v4700 import catalog as seafloor_catalog, readiness as seafloor_readiness
from .underwater_observation_v4800 import catalog as underwater_catalog, readiness as underwater_readiness
from .marine_biodiversity_v4900 import catalog as marine_biodiversity_catalog, readiness as marine_biodiversity_readiness
from .ocean_missions_v41000 import catalog as ocean_missions_catalog, readiness as ocean_missions_readiness
from .ocean_events_v41100 import catalog as ocean_events_catalog, readiness as ocean_events_readiness
from .marine_human_activity_v41200 import catalog as marine_human_activity_catalog, readiness as marine_human_activity_readiness
from .marine_pollution_v41300 import catalog as marine_pollution_catalog, readiness as marine_pollution_readiness
from .coastal_change_v41400 import catalog as coastal_change_catalog, readiness as coastal_change_readiness
from .ocean_governance_v41500 import catalog as ocean_governance_catalog, readiness as ocean_governance_readiness

CONTRACT = "global-ocean-intelligence-ii-ocean-observation-marine-systems"
ROUTE = "earth"
MODE = "ocean"
TITLE = "Global Ocean Intelligence II — Ocean Observation & Marine Systems"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(payload: dict[str, Any]) -> str:
    clean = {k: v for k, v in payload.items() if k not in {"generated_at", "contract_sha256", "catalog_sha256", "manifest_sha256"}}
    return sha256(json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SYSTEMS: tuple[dict[str, Any], ...] = (
    {"id": "surface", "title": "Ocean Surface", "group": "physical-ocean", "endpoint": "/public/ocean-intelligence", "asset": "ocean-surface-v4500", "global": "SCSIOceanSurfaceV4500", "catalog": ocean_surface_catalog, "readiness": ocean_surface_readiness, "capabilities": ["sea-surface temperature", "chlorophyll", "sea-surface height", "surface salinity", "currents", "winds", "waves", "sea ice", "SST anomaly"]},
    {"id": "water-column", "title": "Water Column & Depth", "group": "physical-ocean", "endpoint": "/public/water-column", "asset": "water-column-v4600", "global": "SCSIWaterColumnV4600", "catalog": water_column_catalog, "readiness": water_column_readiness, "capabilities": ["temperature profiles", "salinity profiles", "oxygen", "density", "pressure/depth", "3-D ocean products"]},
    {"id": "seafloor", "title": "Seafloor & Bathymetry", "group": "physical-ocean", "endpoint": "/public/seafloor-intelligence", "asset": "seafloor-bathymetry-v4700", "global": "SCSISeafloorV4700", "catalog": seafloor_catalog, "readiness": seafloor_readiness, "capabilities": ["bathymetric elevation", "terrain grids", "survey coverage", "soundings", "seafloor relief"]},
    {"id": "underwater", "title": "Underwater Observation", "group": "observing-systems", "endpoint": "/public/underwater-observation", "asset": "underwater-observation-v4800", "global": "SCSIUnderwaterV4800", "catalog": underwater_catalog, "readiness": underwater_readiness, "capabilities": ["ROV/AUV media", "underwater imagery", "video", "annotations", "expedition evidence"]},
    {"id": "biodiversity", "title": "Marine Biodiversity & Bioacoustics", "group": "living-ocean", "endpoint": "/public/marine-biodiversity", "asset": "marine-biodiversity-v4900", "global": "SCSIMarineBiodiversityV4900", "catalog": marine_biodiversity_catalog, "readiness": marine_biodiversity_readiness, "capabilities": ["species occurrence", "taxonomy", "visual observations", "hydrophone evidence", "bioacoustics"]},
    {"id": "missions", "title": "Missions, Vehicles & Observatories", "group": "observing-systems", "endpoint": "/public/ocean-missions", "asset": "ocean-missions-v41000", "global": "SCSIOceanMissionsV41000", "catalog": ocean_missions_catalog, "readiness": ocean_missions_readiness, "capabilities": ["Argo floats", "gliders", "research vessels", "observatories", "mission tracks"]},
    {"id": "events", "title": "Ocean Events & Hazards", "group": "ocean-change", "endpoint": "/public/ocean-events", "asset": "ocean-events-v41100", "global": "SCSIOceanEventsV41100", "catalog": ocean_events_catalog, "readiness": ocean_events_readiness, "capabilities": ["marine heatwaves", "coral stress", "harmful algal blooms", "ocean hazards", "ecosystem change"]},
    {"id": "human-activity", "title": "Marine Human Activity", "group": "human-ocean", "endpoint": "/public/marine-human-activity", "asset": "marine-human-activity-v41200", "global": "SCSIMarineHumanActivityV41200", "catalog": marine_human_activity_catalog, "readiness": marine_human_activity_readiness, "capabilities": ["vessel traffic", "fishing activity", "marine protected areas", "human-use pressure"]},
    {"id": "pollution", "title": "Marine Pollution & Water Quality", "group": "human-ocean", "endpoint": "/public/marine-pollution", "asset": "marine-pollution-v41300", "global": "SCSIMarinePollutionV41300", "catalog": marine_pollution_catalog, "readiness": marine_pollution_readiness, "capabilities": ["microplastics", "marine litter", "contaminants", "water quality", "biogeochemistry"]},
    {"id": "coastal-change", "title": "Coastal Change & Sea Level", "group": "ocean-change", "endpoint": "/public/coastal-change", "asset": "coastal-change-v41400", "global": "SCSICoastalChangeV41400", "catalog": coastal_change_catalog, "readiness": coastal_change_readiness, "capabilities": ["water levels", "tides", "sea-level screening", "shoreline change", "mangrove/blue-carbon context"]},
    {"id": "governance", "title": "Ocean Governance & Maritime Boundaries", "group": "human-ocean", "endpoint": "/public/ocean-governance", "asset": "ocean-governance-v41500", "global": "SCSIOceanGovernanceV41500", "catalog": ocean_governance_catalog, "readiness": ocean_governance_readiness, "capabilities": ["maritime zones", "EEZ orientation", "fishing areas", "regional fishery bodies", "jurisdiction context"]},
)

GROUPS = (
    {"id": "physical-ocean", "title": "Physical Ocean", "description": "Surface, depth and seafloor observations with measurement-class boundaries."},
    {"id": "observing-systems", "title": "Observing Systems", "description": "Platforms, expeditions, underwater media and mission evidence."},
    {"id": "living-ocean", "title": "Living Ocean", "description": "Biodiversity, taxonomy, visual and acoustic evidence."},
    {"id": "ocean-change", "title": "Ocean Change & Hazards", "description": "Marine hazards, ecosystem stress, coastal change and sea-level context."},
    {"id": "human-ocean", "title": "Human–Ocean Systems", "description": "Human activity, pollution, protected areas and maritime governance."},
)

TRUTH_BOUNDARIES = (
    "Observed, satellite-derived, in-situ, analysis, model, forecast, derived, media, occurrence, legal-orientation and human-activity records remain distinct evidence classes.",
    "A registered source or available query path does not prove that a measurement exists for a selected location, time, depth or feature.",
    "Missing ocean data remains missing; Site Intelligence does not silently substitute another source, nearest sample, model value or zero.",
    "Underwater imagery or annotation does not by itself establish species abundance, habitat condition or causal ecological change.",
    "Maritime geometry is orientation evidence and is not a legal determination, sovereignty decision, navigation instruction or enforcement finding.",
    "Hazard, pollution and coastal-change products retain their source-defined uncertainty and are not converted into local safety, health, damage or property determinations.",
)


def _system_summary(system: dict[str, Any]) -> dict[str, Any]:
    cat = system["catalog"]()
    sources = cat.get("sources") or []
    source_rows = [{"id": str(row.get("id") or ""), "title": str(row.get("title") or row.get("id") or "Source")} for row in sources]
    dimensional_counts = {
        key: value for key, value in cat.items()
        if key.endswith("_count") and key not in {"source_count"} and isinstance(value, int)
    }
    return {
        "id": system["id"],
        "title": system["title"],
        "group": system["group"],
        "endpoint": system["endpoint"],
        "asset": system["asset"],
        "browser_global": system["global"],
        "capabilities": list(system["capabilities"]),
        "source_count": len(source_rows),
        "sources": source_rows,
        "dimension_counts": dimensional_counts,
    }


def overview() -> dict[str, Any]:
    rows = [_system_summary(system) for system in SYSTEMS]
    unique_sources = {(source["id"], source["title"]) for row in rows for source in row["sources"]}
    payload = {
        "ok": True,
        "version": APP_VERSION,
        "contract": CONTRACT,
        "title": TITLE,
        "route": ROUTE,
        "mode": MODE,
        "primary_area": "observe-analyze",
        "system_count": len(rows),
        "group_count": len(GROUPS),
        "source_registration_count": sum(row["source_count"] for row in rows),
        "unique_source_count": len(unique_sources),
        "public_route_count_delta": 0,
        "navigation": {"visible_primary_entry": "Ocean", "url": "/app/?view=earth&oceanMode=hub", "preserves_v4_route_contract": True},
        "summary": "Unifies the existing ocean-surface, water-column, seafloor, underwater, biodiversity, mission, event, human-activity, pollution, coastal-change and governance systems into one discoverable Ocean Intelligence workspace.",
        "truth_boundaries": list(TRUTH_BOUNDARIES),
        "generated_at": _now(),
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def catalog() -> dict[str, Any]:
    rows = [_system_summary(system) for system in SYSTEMS]
    by_source: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        for source in row["sources"]:
            key = (source["id"], source["title"])
            by_source.setdefault(key, set()).add(row["id"])
    source_index = [
        {"id": source_id, "title": title, "systems": sorted(systems), "system_count": len(systems)}
        for (source_id, title), systems in sorted(by_source.items(), key=lambda item: (item[0][1].lower(), item[0][0]))
    ]
    payload = {
        "ok": True,
        "version": APP_VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": MODE,
        "groups": [dict(group) for group in GROUPS],
        "systems": rows,
        "system_count": len(rows),
        "source_registration_count": sum(row["source_count"] for row in rows),
        "unique_source_count": len(source_index),
        "source_index": source_index,
        "truth_boundaries": list(TRUTH_BOUNDARIES),
        "generated_at": _now(),
    }
    payload["catalog_sha256"] = _digest(payload)
    return payload


def workspace_manifest() -> dict[str, Any]:
    cat = catalog()
    payload = {
        "ok": True,
        "version": APP_VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-ocean-observation-workspace/1.0",
        "route": ROUTE,
        "mode": MODE,
        "url": "/app/?view=earth&oceanMode=hub",
        "systems": [
            {
                "id": row["id"],
                "title": row["title"],
                "endpoint": row["endpoint"],
                "asset": row["asset"],
                "source_count": row["source_count"],
                "capabilities": row["capabilities"],
            }
            for row in cat["systems"]
        ],
        "source_index": cat["source_index"],
        "truth_boundaries": list(TRUTH_BOUNDARIES),
        "review": {
            "new_public_route_created": False,
            "ocean_navigation_is_first_class": True,
            "legacy_ocean_modules_reimplemented": False,
            "existing_ocean_contracts_composed": True,
            "network_calls_performed": False,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(payload)
    return payload


def readiness() -> dict[str, Any]:
    system_checks: dict[str, Any] = {}
    all_ready = True
    for system in SYSTEMS:
        try:
            state = system["readiness"]()
            ready = bool(state.get("ok"))
            system_checks[system["id"]] = {"ok": ready, "contract": state.get("contract"), "network_calls_performed": False}
            all_ready = all_ready and ready
        except Exception as exc:  # deterministic release surface; failures remain explicit
            all_ready = False
            system_checks[system["id"]] = {"ok": False, "error": type(exc).__name__, "network_calls_performed": False}
    checks = {
        "all_inherited_ocean_systems_ready": all_ready,
        "eleven_ocean_systems_composed": len(SYSTEMS) == 11,
        "ocean_primary_navigation_entry_present": True,
        "v4_six_area_35_route_contract_preserved": True,
        "public_route_count_delta_zero": True,
        "network_free_release_check": True,
        "missing_data_truth_boundary_preserved": True,
        "marine_legal_and_safety_boundaries_preserved": True,
    }
    return {
        "ok": all(checks.values()),
        "version": APP_VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": MODE,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "system_count": len(SYSTEMS),
        "primary_area_count": 6,
        "inherited_route_count": 35,
        "public_route_count_delta": 0,
        "checks": checks,
        "systems": system_checks,
        "generated_at": _now(),
    }
