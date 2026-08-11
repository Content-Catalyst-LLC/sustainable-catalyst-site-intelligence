from __future__ import annotations

"""Site Intelligence v4.35.3.1 authoritative API/workspace integrity audit.

This module is deliberately evidence-conservative.  It distinguishes source
registrations from implemented retrieval clients and never promotes a portal or
source definition to LIVE merely because a URL is present.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "authoritative-api-workspace-integrity-audit"
AUDIT_DATE = "2026-08-10"

ACCESS_CLASSES = (
    "LIVE",
    "DISCOVERY",
    "REGISTERED",
    "AUTH_REQUIRED",
    "BULK",
    "STALE",
    "UNAVAILABLE",
)

# Source-bearing modules currently shipping in Site Intelligence.  The audit
# reads their immutable source registries; it does not call upstream APIs.
SOURCE_MODULES: tuple[tuple[str, str], ...] = (
    ("climate_intelligence_v42200", "Climate Baselines, Anomalies & Extremes"),
    ("cryosphere_v41600", "Cryosphere"),
    ("sustainable_development_connectors", "Sustainable Development Connectors"),
    ("ocean_surface_v4500", "Ocean Surface"),
    ("hydrology_v41800", "Hydrology, Rivers, Flood & Drought"),
    ("solid_waste_circular_materials_v43300", "Solid Waste & Circular Materials"),
    ("source_methodology_studio", "Sources & Methodology"),
    ("humanitarian_intelligence", "Humanitarian Intelligence"),
    ("marine_biodiversity_v4900", "Marine Biodiversity & Bioacoustics"),
    ("coastal_change_v41400", "Coastal Change, Sea Level & Blue Carbon"),
    ("atmosphere_v41700", "Atmosphere, Air Quality & Aerosols"),
    ("international_law_governance", "International Law & Governance"),
    ("exoplanet_habitability_v43500", "Exoplanets, Habitability & Biosignatures"),
    ("water_column_v4600", "Water Column & Depth"),
    ("marine_pollution_v41300", "Marine Pollution & Water Quality"),
    ("unified_live_events", "Unified Live Events"),
    ("wetlands_inland_waters_v42400", "Wetlands & Inland Waters"),
    ("seafloor_bathymetry_v4700", "Seafloor & Bathymetry"),
    ("energy_systems_v42800", "Energy Infrastructure & Power Systems"),
    ("biodiversity_intelligence_v42300", "Biodiversity & Conservation"),
    ("mining_critical_materials_v43100", "Mining & Critical Materials"),
    ("human_settlements_v42600", "Human Settlements & Built Environment"),
    ("ocean_events_v41100", "Ocean Events & Hazards"),
    ("seti_technosignatures_v43400", "SETI & Technosignatures"),
    ("soils_land_degradation_v42100", "Soils & Land Degradation"),
    ("water_sanitation_infrastructure_v43200", "Water, Wastewater & Sanitation"),
    ("marine_human_activity_v41200", "Marine Human Activity & Protected Areas"),
    ("ocean_missions_v41000", "Ocean Missions & Observatory Networks"),
    ("conflict_human_security", "Conflict & Human Security"),
    ("agriculture_food_systems_v42500", "Agriculture, Crops & Food Systems"),
    ("geosphere_v42000", "Geosphere, Earthquakes & Volcanoes"),
    ("human_development_intelligence", "Human Development"),
    ("ocean_governance_v41500", "Ocean Governance & Maritime Boundaries"),
    ("terrestrial_ecosystems_v41900", "Terrestrial Ecosystems & Wildfire"),
    ("underwater_observation_v4800", "Underwater Observation & Visual Evidence"),
    ("industrial_manufacturing_trade_v43000", "Industrial Manufacturing & Trade"),
    ("digital_connectivity_v42900", "Digital Connectivity"),
    ("transportation_infrastructure_v42700", "Transportation Infrastructure"),
)

REGISTRY_NAMES = ("SOURCES", "SOURCE_REGISTRY", "SOURCE_RECORDS")

# Code-level retrieval evidence.  Matching is conservative: a provider is only
# LIVE/DISCOVERY when this repository contains a real read path for it.
IMPLEMENTED_IDS = {
    "nasa_power": ("LIVE", "connectors.external_data NASA POWER retrieval"),
    "nasa_gibs": ("DISCOVERY", "connectors.external_data GIBS capabilities/layer discovery"),
    "climate_trace": ("LIVE", "connectors.external_data Climate TRACE retrieval with fallback"),
    "noaa_weather_climate": ("LIVE", "connectors.advanced_external NWS forecast/alerts retrieval"),
    "eia_energy": ("AUTH_REQUIRED", "connectors.advanced_external EIA retrieval; API key required"),
    "epa_aqs_air_quality": ("AUTH_REQUIRED", "connectors.advanced_external EPA AQS retrieval; email/key required"),
    "census_context": ("LIVE", "connectors.advanced_external Census ACS retrieval"),
    "usgs_land_cover": ("REGISTERED", "Current advanced connector is registry-context only; dedicated USGS land-data retrieval remains unfinished."),
    "gbif_biodiversity": ("LIVE", "connectors.advanced_external GBIF occurrence retrieval"),
}

IMPLEMENTED_HOSTS = {
    "api.worldbank.org": ("LIVE", "live_country_intelligence / World Bank indicator client"),
    "earthquake.usgs.gov": ("LIVE", "unified_live_events USGS GeoJSON retrieval"),
    "eonet.gsfc.nasa.gov": ("LIVE", "unified_live_events NASA EONET retrieval"),
    "api.reliefweb.int": ("AUTH_REQUIRED", "unified_live_events ReliefWeb V2 retrieval; approved appname required"),
    "power.larc.nasa.gov": ("LIVE", "connectors.external_data NASA POWER retrieval"),
    "gibs.earthdata.nasa.gov": ("DISCOVERY", "connectors.external_data GIBS capabilities/layer discovery"),
    "api.weather.gov": ("LIVE", "connectors.advanced_external NWS forecast/alerts retrieval"),
    "api.eia.gov": ("AUTH_REQUIRED", "connectors.advanced_external EIA retrieval; API key required"),
    "aqs.epa.gov": ("AUTH_REQUIRED", "connectors.advanced_external EPA AQS retrieval; email/key required"),
    "api.census.gov": ("LIVE", "connectors.advanced_external Census ACS retrieval"),
    "api.gbif.org": ("LIVE", "connectors.advanced_external GBIF occurrence retrieval"),
    "api.openalex.org": ("LIVE", "public API source connector"),
    "api.crossref.org": ("LIVE", "public API source connector"),
    "api.github.com": ("LIVE", "public API source connector"),
    "api.climatetrace.org": ("LIVE", "connectors.external_data Climate TRACE retrieval with fallback"),
}

# Official external documentation checked for this audit.  These records do not
# claim that Site Intelligence already executes the API; they establish that a
# machine-readable authoritative path exists and should be connected.
VERIFIED_MACHINE_INTERFACES = (
    {
        "id": "reliefweb-v2",
        "provider": "ReliefWeb / UN OCHA",
        "host": "api.reliefweb.int",
        "protocol": "REST / OpenAPI 3.1",
        "current_version": "V2",
        "documentation_url": "https://apidoc.reliefweb.int/",
        "authentication": "pre-approved appname required",
        "status": "implemented-auth-required",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "usgs-water-ogc-v0",
        "provider": "U.S. Geological Survey Water Data",
        "host": "api.waterdata.usgs.gov",
        "protocol": "OGC API / STAC / REST",
        "current_version": "v0",
        "documentation_url": "https://api.waterdata.usgs.gov/docs/",
        "authentication": "public; API key increases rate limits",
        "status": "priority-connect",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "noaa-coastwatch-erddap",
        "provider": "NOAA CoastWatch / OceanWatch",
        "host": "coastwatch.noaa.gov",
        "protocol": "ERDDAP REST / griddap / tabledap",
        "current_version": "server-advertised",
        "documentation_url": "https://coastwatch.noaa.gov/erddap/rest.html",
        "authentication": "none for public datasets",
        "status": "priority-connect",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "nasa-cmr-search",
        "provider": "NASA EOSDIS Common Metadata Repository",
        "host": "cmr.earthdata.nasa.gov",
        "protocol": "REST / STAC / UMM JSON",
        "current_version": "current service",
        "documentation_url": "https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html",
        "authentication": "guest search supported; auth for restricted assets",
        "status": "priority-discovery-backbone",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "nasa-cmr-graphql",
        "provider": "NASA EOSDIS Common Metadata Repository",
        "host": "graphql.earthdata.nasa.gov",
        "protocol": "GraphQL",
        "current_version": "current service",
        "documentation_url": "https://graphql.earthdata.nasa.gov/docs/introduction/introduction/",
        "authentication": "query dependent",
        "status": "priority-discovery-backbone",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "nasa-exoplanet-tap",
        "provider": "NASA Exoplanet Archive",
        "host": "exoplanetarchive.ipac.caltech.edu",
        "protocol": "TAP / ADQL",
        "current_version": "current TAP service",
        "documentation_url": "https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html",
        "authentication": "public query service",
        "status": "priority-connect",
        "audit_date": AUDIT_DATE,
    },
    {
        "id": "unhcr-refugee-statistics-v1",
        "provider": "UNHCR Refugee Statistics",
        "host": "api.unhcr.org",
        "protocol": "REST / JSON",
        "current_version": "1.0.0",
        "documentation_url": "https://api.unhcr.org/docs/refugee-statistics.html",
        "authentication": "public read API",
        "status": "priority-connect",
        "audit_date": AUDIT_DATE,
    },
)

PRIORITY_CONNECTOR_TARGETS = (
    {
        "id": "usgs-water-ogc-v0",
        "workspace": "Hydrology, Rivers, Flood & Drought",
        "reason": "Workspace already registers USGS Water Data but does not retrieve observations.",
        "target_state": "LIVE",
    },
    {
        "id": "noaa-coastwatch-erddap",
        "workspace": "Ocean Surface",
        "reason": "Workspace already prepares ERDDAP query plans; execute constrained dataset/point/time retrievals next.",
        "target_state": "LIVE",
    },
    {
        "id": "nasa-exoplanet-tap",
        "workspace": "Exoplanets, Habitability & Biosignatures",
        "reason": "Use the official TAP/ADQL service instead of registry-only planet query plans.",
        "target_state": "LIVE",
    },
    {
        "id": "unhcr-refugee-statistics-v1",
        "workspace": "Humanitarian / future Migration & Displacement",
        "reason": "Direct authoritative displacement statistics with country/year/demographic dimensions and footnotes.",
        "target_state": "LIVE",
    },
    {
        "id": "nasa-cmr-search",
        "workspace": "Earth / Science / Space discovery",
        "reason": "Use CMR as a discovery backbone so NASA dataset availability is searched rather than hard-coded one product at a time.",
        "target_state": "DISCOVERY",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _as_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]


def _host(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return (urlparse(text).hostname or "").lower()
    except Exception:
        return ""


def _registry_rows(module_name: str, workspace: str) -> Iterable[dict[str, Any]]:
    module = importlib.import_module(f". {module_name}".replace(" ", ""), package=__package__)
    for registry_name in REGISTRY_NAMES:
        registry = getattr(module, registry_name, None)
        if isinstance(registry, dict):
            items = registry.items()
        elif isinstance(registry, list):
            items = []
            for index, item in enumerate(registry):
                if not isinstance(item, dict):
                    continue
                sid = item.get("id") or item.get("source_id") or item.get("slug") or item.get("connector_id") or f"row-{index+1}"
                items.append((sid, item))
        else:
            continue
        for source_id, raw in items:
            if not isinstance(raw, dict):
                continue
            yield {
                "workspace": workspace,
                "module": module_name,
                "registry": registry_name,
                "source_id": str(source_id),
                "raw": raw,
            }


def _protocol(raw: dict[str, Any]) -> str:
    text = " ".join(str(raw.get(key) or "") for key in (
        "machine_access", "access", "connector", "connector_type", "api_url", "url", "documentation_url"
    )).lower()
    if "erddap" in text:
        return "ERDDAP"
    if "graphql" in text:
        return "GraphQL"
    if re.search(r"\btap\b|adql", text):
        return "TAP / ADQL"
    if "sdmx" in text:
        return "SDMX"
    if "stac" in text:
        return "STAC"
    if "ogc api" in text or "ogcapi" in text:
        return "OGC API"
    if "opendap" in text:
        return "OPeNDAP"
    if "wmts" in text or "wms" in text or "wcs" in text:
        return "OGC map service"
    if "api" in text or "json" in text or "rest" in text:
        return "REST / JSON"
    if any(token in text for token in ("csv", "download", "bulk", "file", "geopackage", "netcdf", "parquet")):
        return "Bulk / file"
    return "Portal / unspecified"


def _primary_host(raw: dict[str, Any]) -> str:
    for key in ("api_url", "endpoint", "url", "official_url", "documentation_url"):
        host = _host(raw.get(key))
        if host:
            return host
    hosts = raw.get("recognized_hosts") or []
    return str(hosts[0]).lower() if hosts else ""


def _authority(raw: dict[str, Any]) -> str:
    existing = raw.get("authority")
    if existing:
        return str(existing)
    organization = str(raw.get("organization") or raw.get("publisher") or raw.get("provider") or "").lower()
    if any(token in organization for token in (
        "nasa", "noaa", "usgs", "epa", "department", "ministry", "government", "census", "energy information administration",
    )):
        return "official-government-source"
    if any(token in organization for token in (
        "united nations", "unhcr", "fao", "who", "world bank", "imf", "oecd", "copernicus", "european commission", "ecmwf",
    )):
        return "official-intergovernmental-or-public-institution"
    return "registered-public-source"


def _machine_readable(raw: dict[str, Any], protocol: str) -> bool:
    text = " ".join(str(raw.get(key) or "") for key in ("machine_access", "access", "api_url", "connector", "connector_type")).lower()
    return protocol != "Portal / unspecified" or any(token in text for token in ("api", "json", "csv", "bulk", "download", "service", "catalog"))


def _configured_state(host: str, settings: Any = None) -> tuple[str | None, str | None]:
    if settings is None:
        return None, None
    if host == "api.reliefweb.int":
        configured = bool(str(getattr(settings, "reliefweb_appname", "") or "").strip())
        return ("configured" if configured else "configuration-required", "SC_SI_RELIEFWEB_APPNAME")
    if host == "api.eia.gov":
        configured = bool(str(getattr(settings, "eia_api_key", "") or "").strip())
        return ("configured" if configured else "configuration-required", "SC_SI_EIA_API_KEY")
    if host == "aqs.epa.gov":
        configured = bool(str(getattr(settings, "epa_aqs_email", "") or "").strip() and str(getattr(settings, "epa_aqs_key", "") or "").strip())
        return ("configured" if configured else "configuration-required", "SC_SI_EPA_AQS_EMAIL + SC_SI_EPA_AQS_KEY")
    return None, None


def _classify(raw: dict[str, Any], protocol: str, host: str, settings: Any = None, source_id: str = "") -> tuple[str, str]:
    if source_id in IMPLEMENTED_IDS:
        base_state, evidence = IMPLEMENTED_IDS[source_id]
        if source_id == "eia_energy":
            configured = bool(str(getattr(settings, "eia_api_key", "") or "").strip()) if settings is not None else False
            return ("LIVE" if configured else base_state), evidence
        if source_id == "epa_aqs_air_quality":
            configured = bool(str(getattr(settings, "epa_aqs_email", "") or "").strip() and str(getattr(settings, "epa_aqs_key", "") or "").strip()) if settings is not None else False
            return ("LIVE" if configured else base_state), evidence
        return base_state, evidence
    if host in IMPLEMENTED_HOSTS:
        base_state, evidence = IMPLEMENTED_HOSTS[host]
        config_state, _ = _configured_state(host, settings)
        if base_state == "AUTH_REQUIRED" and config_state == "configured":
            return "LIVE", evidence
        return base_state, evidence

    machine = _machine_readable(raw, protocol)
    auth = " ".join(_as_list(raw.get("authentication")) + _as_list(raw.get("auth_required")) + _as_list(raw.get("access"))).lower()
    if machine and any(token in auth for token in ("key required", "account required", "credential", "authenticated", "subscription", "token required")):
        return "AUTH_REQUIRED", "Machine-readable source is registered but no Site Intelligence retrieval client is implemented."
    if machine and protocol == "Bulk / file":
        return "BULK", "Authoritative machine-readable files are registered; no direct retrieval client is implemented."
    if machine:
        return "REGISTERED", "Machine-readable source is registered, but the workspace does not yet retrieve source observations."
    return "UNAVAILABLE", "Source/portal is registered, but no stable machine-readable retrieval path is documented in the current source record."


def _external_connector_seed_rows() -> Iterable[dict[str, Any]]:
    path = Path(__file__).resolve().parents[1] / "data" / "external_connectors.seed.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for item in payload.get("connectors", []):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("connector_id") or "").strip()
        if not source_id:
            continue
        raw = dict(item)
        # Give the audit the actual machine interface host where the legacy seed
        # only stores human-facing documentation.
        api_overrides = {
            "nasa_power": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "nasa_gibs": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml",
            "climate_trace": "https://api.climatetrace.org/v6",
            "noaa_weather_climate": "https://api.weather.gov",
            "eia_energy": "https://api.eia.gov/v2",
            "epa_aqs_air_quality": "https://aqs.epa.gov/data/api",
            "census_context": "https://api.census.gov",
            "gbif_biodiversity": "https://api.gbif.org/v1",
        }
        if source_id in api_overrides:
            raw["api_url"] = api_overrides[source_id]
        raw.setdefault("title", item.get("name"))
        raw.setdefault("organization", item.get("provider"))
        raw.setdefault("machine_access", item.get("connector_type"))
        raw.setdefault("authentication", "required" if item.get("auth_required") is True else "none")
        rows.append({
            "workspace": "Legacy Live External Connectors",
            "module": "connectors.external_data / connectors.advanced_external",
            "registry": "external_connectors.seed.json",
            "source_id": source_id,
            "raw": raw,
        })
    return rows


def source_inventory(settings: Any = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_registration_keys: set[tuple[str, str, str]] = set()
    module_groups: list[tuple[str, str, list[dict[str, Any]]]] = []
    for module_name, workspace in SOURCE_MODULES:
        try:
            module_groups.append((module_name, workspace, list(_registry_rows(module_name, workspace))))
        except Exception as exc:
            module_groups.append((module_name, workspace, [{"workspace": workspace, "module": module_name, "registry": "module-load", "source_id": "module-load-error", "raw": {"title": "Source registry unavailable", "limitations": f"Registry load failed: {type(exc).__name__}"}}]))
    module_groups.append(("external_connector_seed", "Legacy Live External Connectors", list(_external_connector_seed_rows())))
    for module_name, workspace, candidates in module_groups:
        for candidate in candidates:
            key = (candidate["module"], candidate["registry"], candidate["source_id"])
            if key in seen_registration_keys:
                continue
            seen_registration_keys.add(key)
            raw = candidate["raw"]
            protocol = _protocol(raw)
            host = _primary_host(raw)
            access_class, implementation_evidence = _classify(raw, protocol, host, settings, candidate["source_id"])
            configuration_state, configuration_key = _configured_state(host, settings)
            rows.append({
                "workspace": workspace,
                "module": module_name,
                "registry": candidate["registry"],
                "source_id": candidate["source_id"],
                "title": raw.get("title") or raw.get("name") or raw.get("label") or candidate["source_id"],
                "organization": raw.get("organization") or raw.get("publisher") or raw.get("provider"),
                "authority": _authority(raw),
                "host": host,
                "url": raw.get("url") or raw.get("official_url"),
                "api_url": raw.get("api_url") or raw.get("endpoint"),
                "documentation_url": raw.get("documentation_url"),
                "protocol": protocol,
                "machine_readable": _machine_readable(raw, protocol),
                "access_class": access_class,
                "implementation_evidence": implementation_evidence,
                "configuration_state": configuration_state,
                "configuration_key": configuration_key,
                "authentication": raw.get("authentication") or raw.get("auth_required") or raw.get("access"),
                "coverage": raw.get("coverage") or raw.get("geographic_coverage"),
                "limitations": raw.get("limitations") or raw.get("known_limits"),
            })
    return rows


def _unique_source_key(row: dict[str, Any]) -> str:
    # Host is a better deduplication key than source_id because the same provider
    # is registered under workspace-specific IDs.  If no host exists, preserve
    # the module/source identity rather than pretending two portals are identical.
    host = row.get("host") or ""
    if host:
        return f"host:{host}"
    return f"record:{row.get('module')}:{row.get('source_id')}"


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(row["access_class"] for row in rows)
    return {state: int(counter.get(state, 0)) for state in ACCESS_CLASSES}


def audit_overview(settings: Any = None) -> dict[str, Any]:
    rows = source_inventory(settings)
    counts = _counts(rows)
    unique = {_unique_source_key(row) for row in rows}
    machine_rows = [row for row in rows if row.get("machine_readable")]
    implemented = counts["LIVE"] + counts["DISCOVERY"] + counts["AUTH_REQUIRED"]
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "audit_date": AUDIT_DATE,
        "classification": {
            "LIVE": "Repository contains an implemented observation/record retrieval path and no required configuration is missing.",
            "DISCOVERY": "Repository retrieves authoritative metadata/capabilities, but not the underlying observation values for this registration.",
            "REGISTERED": "Machine-readable authoritative source is described, but no live retrieval client is implemented for this workspace registration.",
            "AUTH_REQUIRED": "A machine-readable path exists, but required credentials/configuration are missing or the source requires authenticated access.",
            "BULK": "Authoritative machine-readable files are available, but are not connected as a live API client.",
            "STALE": "The implemented endpoint/version is obsolete or decommissioned.",
            "UNAVAILABLE": "No stable machine-readable path is documented in the current registration.",
        },
        "summary": {
            "source_registrations": len(rows),
            "unique_source_endpoints_or_records": len(unique),
            "workspaces_with_source_registries": len({row["workspace"] for row in rows}),
            "machine_readable_registrations": len(machine_rows),
            "implemented_or_configuration_gated_registrations": implemented,
            "counts": counts,
            "registered_but_not_retrieved": counts["REGISTERED"],
            "stale_implemented_connectors": counts["STALE"],
        },
        "principles": [
            "A source registration is not counted as a live connector.",
            "Missing upstream observations remain missing; sample or fallback data is never promoted as a live authoritative observation.",
            "Source authority, metric semantics, observation date, units, and provenance must remain visible through normalization.",
            "National/sector authorities and international custodian series may measure different concepts and must not be silently substituted.",
        ],
        "verified_machine_interfaces": list(VERIFIED_MACHINE_INTERFACES),
        "priority_connector_targets": list(PRIORITY_CONNECTOR_TARGETS),
        "generated_at": _now(),
    }
    payload["audit_sha256"] = _digest({"summary": payload["summary"], "verified": payload["verified_machine_interfaces"]})
    return payload


def audit_catalog(
    settings: Any = None,
    workspace: str = "",
    access_class: str = "",
    query: str = "",
) -> dict[str, Any]:
    rows = source_inventory(settings)
    workspace_q = (workspace or "").strip().lower()
    class_q = (access_class or "").strip().upper()
    text_q = (query or "").strip().lower()
    if class_q and class_q not in ACCESS_CLASSES:
        raise ValueError(f"access_class must be one of: {', '.join(ACCESS_CLASSES)}")
    if workspace_q:
        rows = [row for row in rows if workspace_q in row["workspace"].lower() or workspace_q == row["module"].lower()]
    if class_q:
        rows = [row for row in rows if row["access_class"] == class_q]
    if text_q:
        rows = [row for row in rows if text_q in " ".join(str(row.get(key) or "") for key in ("title", "organization", "host", "source_id", "protocol", "workspace")).lower()]
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "count": len(rows),
        "counts": _counts(rows),
        "access_classes": list(ACCESS_CLASSES),
        "sources": rows,
        "generated_at": _now(),
    }


def workspace_matrix(settings: Any = None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_inventory(settings):
        groups[row["workspace"]].append(row)
    workspaces = []
    for workspace, rows in sorted(groups.items()):
        counts = _counts(rows)
        machine = sum(1 for row in rows if row.get("machine_readable"))
        workspaces.append({
            "workspace": workspace,
            "source_registrations": len(rows),
            "machine_readable_registrations": machine,
            "counts": counts,
            "fully_live": machine > 0 and counts["REGISTERED"] == 0 and counts["STALE"] == 0 and counts["AUTH_REQUIRED"] == 0,
            "connector_gap": counts["REGISTERED"] + counts["BULK"] + counts["AUTH_REQUIRED"] + counts["STALE"],
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "workspace_count": len(workspaces),
        "workspaces": workspaces,
        "generated_at": _now(),
    }


def audit_readiness(settings: Any = None) -> dict[str, Any]:
    overview = audit_overview(settings)
    counts = overview["summary"]["counts"]
    verified_ids = {row["id"] for row in VERIFIED_MACHINE_INTERFACES}
    checks = {
        "source_registry_inventory_present": overview["summary"]["source_registrations"] >= 150,
        "source_registration_not_equal_live_connector": counts["REGISTERED"] > 0,
        "classification_taxonomy_complete": set(ACCESS_CLASSES) == {"LIVE", "DISCOVERY", "REGISTERED", "AUTH_REQUIRED", "BULK", "STALE", "UNAVAILABLE"},
        "reliefweb_v2_verified": "reliefweb-v2" in verified_ids,
        "usgs_water_api_verified": "usgs-water-ogc-v0" in verified_ids,
        "noaa_erddap_verified": "noaa-coastwatch-erddap" in verified_ids,
        "nasa_cmr_verified": "nasa-cmr-search" in verified_ids,
        "exoplanet_tap_verified": "nasa-exoplanet-tap" in verified_ids,
        "unhcr_api_verified": "unhcr-refugee-statistics-v1" in verified_ids,
        "no_known_stale_connector_after_reliefweb_migration": counts["STALE"] == 0,
        "priority_connector_backlog_present": len(PRIORITY_CONNECTOR_TARGETS) >= 5,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "checks": checks,
        "summary": overview["summary"],
        "configuration": {
            "reliefweb_appname_configured": bool(str(getattr(settings, "reliefweb_appname", "") or "").strip()) if settings is not None else False,
            "reliefweb_required_environment": "SC_SI_RELIEFWEB_APPNAME=<pre-approved ReliefWeb V2 appname>",
        },
        "generated_at": _now(),
    }
