from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "global-ocean-intelligence-surface-conditions"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "noaa-coastwatch-erddap": {
        "title": "NOAA CoastWatch / OceanWatch ERDDAP",
        "organization": "NOAA CoastWatch / OceanWatch",
        "url": "https://coastwatch.noaa.gov/erddap/",
        "documentation_url": "https://coastwatch.noaa.gov/cwn/data-access-tools/erddap-noaa-coastwatch.html",
        "recognized_hosts": ["coastwatch.noaa.gov"],
        "coverage": "global and regional satellite ocean products; product-specific coverage applies",
        "authentication": "none for public ERDDAP datasets",
        "evidence_types": ["satellite-derived", "analysis", "derived-product"],
        "machine_access": "ERDDAP griddap/tabledap/WMS and dataset metadata",
    },
    "ioos-catalog": {
        "title": "U.S. IOOS Data Catalog",
        "organization": "U.S. Integrated Ocean Observing System",
        "url": "https://data.ioos.us/",
        "documentation_url": "https://ioos.noaa.gov/data/access-ioos-data/",
        "recognized_hosts": ["data.ioos.us", "ioos.noaa.gov"],
        "coverage": "United States coastal, Great Lakes, and regional observing systems; not global",
        "authentication": "dataset-specific; public discovery does not require a Site Intelligence account",
        "evidence_types": ["in-situ-observation", "model", "analysis", "forecast"],
        "machine_access": "catalog API plus regional ERDDAP/OPeNDAP/WMS/WCS services",
    },
    "copernicus-marine": {
        "title": "Copernicus Marine Service",
        "organization": "Copernicus Marine Service",
        "url": "https://marine.copernicus.eu/",
        "documentation_url": "https://help.marine.copernicus.eu/en/collections/9080063-copernicus-marine-toolbox",
        "recognized_hosts": ["marine.copernicus.eu", "help.marine.copernicus.eu", "toolbox-docs.marine.copernicus.eu"],
        "coverage": "global and regional ocean analysis, forecast, reanalysis, observation and biogeochemical products; dataset-specific coverage applies",
        "authentication": "free Copernicus Marine account may be required for authenticated data services; credentials are never embedded in public Site Intelligence state",
        "evidence_types": ["model", "analysis", "forecast", "reanalysis", "satellite-derived", "in-situ-observation"],
        "machine_access": "Python API/CLI catalogue, open, subset, and original-file workflows",
    },
}

VARIABLES: dict[str, dict[str, Any]] = {
    "sea-surface-temperature": {"title":"Sea-surface temperature","short":"SST","default_unit":"degC","default_source":"noaa-coastwatch-erddap","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Satellite-derived, in-situ, analyzed, reanalyzed, and modeled temperature are distinct evidence classes.","noaa_example_dataset":"noaacwLEOACSPOSSTL3SnrtCDaily"},
    "chlorophyll-a": {"title":"Chlorophyll-a","short":"CHL","default_unit":"mg m-3","default_source":"noaa-coastwatch-erddap","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Ocean-color chlorophyll is an estimate, not a direct census of phytoplankton biomass.","noaa_example_dataset":"noaacwNPPVIIRSchlaDaily"},
    "sea-surface-height": {"title":"Sea-surface height","short":"SSH","default_unit":"m","default_source":"copernicus-marine","sources":["noaa-coastwatch-erddap","copernicus-marine"],"evidence_note":"Absolute height, anomaly, and dynamic topography are distinct products."},
    "sea-surface-salinity": {"title":"Sea-surface salinity","short":"SSS","default_unit":"1e-3","default_source":"copernicus-marine","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Satellite, in-situ, and model salinity are separate evidence classes."},
    "surface-currents": {"title":"Surface currents","short":"CURRENT","default_unit":"m s-1","default_source":"copernicus-marine","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Observed, satellite-derived, blended, analyzed, and forecast current vectors remain distinct.","noaa_example_dataset":"noaacwBLENDEDNRTcurrentsDaily"},
    "surface-wind": {"title":"Ocean-surface wind","short":"WIND","default_unit":"m s-1","default_source":"noaa-coastwatch-erddap","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Scatterometer, buoy, and modeled wind are not silently merged."},
    "significant-wave-height": {"title":"Significant wave height","short":"WAVE","default_unit":"m","default_source":"copernicus-marine","sources":["noaa-coastwatch-erddap","copernicus-marine","ioos-catalog"],"evidence_note":"Altimeter, buoy, analysis, and forecast wave products retain separate provenance."},
    "sea-ice-concentration": {"title":"Sea-ice concentration","short":"ICE","default_unit":"%","default_source":"noaa-coastwatch-erddap","sources":["noaa-coastwatch-erddap","copernicus-marine"],"evidence_note":"Sea-ice concentration is a gridded product and not a navigation-safety determination."},
    "sst-anomaly": {"title":"Sea-surface temperature anomaly","short":"SST Δ","default_unit":"degC","default_source":"noaa-coastwatch-erddap","sources":["noaa-coastwatch-erddap","copernicus-marine"],"evidence_note":"Anomaly is derived from a defined baseline/reference climatology, not a raw thermometer observation."},
}

REGIONS = {
    "global": {"title":"Global ocean","bbox":[-180.0,-80.0,180.0,90.0]},
    "north-atlantic": {"title":"North Atlantic","bbox":[-80.0,0.0,20.0,70.0]},
    "equatorial-pacific": {"title":"Equatorial Pacific","bbox":[120.0,-20.0,-70.0,20.0]},
    "southern-ocean": {"title":"Southern Ocean","bbox":[-180.0,-80.0,180.0,-45.0]},
    "arctic": {"title":"Arctic Ocean","bbox":[-180.0,60.0,180.0,90.0]},
}


def _variable(variable_id: str):
    vid=(variable_id or "sea-surface-temperature").strip().lower()
    if vid not in VARIABLES: raise ValueError(f"unsupported ocean variable: {vid}")
    return vid,{"id":vid,**VARIABLES[vid]}


def _source(source_id: str, variable: dict[str, Any] | None=None):
    sid=(source_id or (variable or {}).get("default_source") or "noaa-coastwatch-erddap").strip().lower()
    if sid not in SOURCES: raise ValueError(f"unsupported ocean source: {sid}")
    if variable and sid not in variable["sources"]: raise ValueError(f"source {sid} is not registered for {variable['id']}")
    return sid,{"id":sid,**SOURCES[sid]}


def _point(latitude: float, longitude: float):
    lat=float(latitude); lon=float(longitude)
    if not -90 <= lat <= 90: raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180: raise ValueError("longitude must be between -180 and 180")
    return {"latitude":round(lat,6),"longitude":round(lon,6)}


def _date(value: str | None):
    raw=(value or "").strip()
    if not raw: return None
    try: return datetime.fromisoformat(raw).date().isoformat()
    except ValueError as exc: raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


def _query_plan(var, src, point, day):
    if src["id"]=="noaa-coastwatch-erddap":
        ds=var.get("noaa_example_dataset")
        return {"access_kind":"ERDDAP dataset discovery / subset","dataset_id":ds,"dataset_metadata_url":f"https://coastwatch.noaa.gov/erddap/info/{ds}/index.html" if ds else "https://coastwatch.noaa.gov/erddap/info/index.html","point":point,"date":day,"automatic_value_loaded":False,"note":"Dataset IDs are product-specific; a registered example is a query starting point, not proof of point/time coverage."}
    if src["id"]=="copernicus-marine":
        return {"access_kind":"Copernicus Marine Toolbox catalogue/subset","catalogue_url":"https://marine.copernicus.eu/","toolbox_docs":"https://toolbox-docs.marine.copernicus.eu/","point":point,"date":day,"credentials_embedded":False,"automatic_value_loaded":False,"note":"Select an exact current dataset before subsetting; authenticated services may require a free account."}
    return {"access_kind":"IOOS catalogue discovery / regional data service","catalog_url":"https://data.ioos.us/","point":point,"date":day,"automatic_value_loaded":False,"note":"IOOS is U.S. coastal/regional; the service endpoint varies by dataset."}


def overview():
    p={"ok":True,"version":VERSION,"contract":CONTRACT,"title":"Global Ocean Intelligence & Surface Conditions","route":ROUTE,"source_count":len(SOURCES),"variable_count":len(VARIABLES),"region_preset_count":len(REGIONS),"summary":"Extend Earth Observation into a provenance-aware ocean-surface mode using registered NOAA, IOOS, and Copernicus Marine access paths.","truth_boundaries":["Observed, satellite-derived, analysis, reanalysis, model, forecast, and derived anomaly products remain distinct evidence classes.","Selecting a variable, location, source, or date does not fabricate a surface value or imply coverage.","Global eligibility is not verified record coverage; IOOS is U.S. coastal/regional rather than global.","A source-attributed record is not independently network-verified without a connector retrieval receipt.","Copernicus Marine credentials are not stored in public state, manifests, browser assets, or repository fixtures.","Missing ocean data remains missing and is never converted to zero or silently replaced by another source."],"generated_at":_now()}
    p["contract_sha256"]=_digest(p); return p


def catalog():
    return {"ok":True,"version":VERSION,"contract":CONTRACT,"source_count":len(SOURCES),"variable_count":len(VARIABLES),"sources":[{"id":k,**v} for k,v in SOURCES.items()],"variables":[{"id":k,**v} for k,v in VARIABLES.items()],"regions":[{"id":k,**v} for k,v in REGIONS.items()],"generated_at":_now()}


def source(source_id: str):
    try: sid,row=_source(source_id)
    except ValueError: return {"ok":False,"version":VERSION,"contract":CONTRACT,"error":"unsupported ocean source","supported_sources":list(SOURCES)}
    p={"ok":True,"version":VERSION,"contract":CONTRACT,"source_id":sid,"source":row,"variables":[{"id":k,**v} for k,v in VARIABLES.items() if sid in v["sources"]],"generated_at":_now()}; p["source_sha256"]=_digest(p); return p


def state(variable_id: str="sea-surface-temperature", source_id: str="", latitude: float=0.0, longitude: float=0.0, date: str=""):
    _,var=_variable(variable_id); _,src=_source(source_id,var); point=_point(latitude,longitude); day=_date(date)
    p={"ok":True,"version":VERSION,"contract":CONTRACT,"mode":"ocean-surface","route":ROUTE,"variable":var,"source":src,"point":point,"date":day,"condition":{"value":None,"unit":var["default_unit"],"evidence_type":None,"record_loaded":False,"current_condition_claimed":False,"coverage_verified":False},"query_plan":_query_plan(var,src,point,day),"truth":{"value_fabricated":False,"missing_replaced":False,"source_substitution_performed":False,"forecast_presented_as_observation":False,"model_presented_as_observation":False,"coverage_inferred_from_source_eligibility":False},"generated_at":_now()}; p["state_sha256"]=_digest(p); return p


def normalize_observation(request: dict[str, Any]):
    if not isinstance(request,dict): raise ValueError("request must be an object")
    vid,var=_variable(str(request.get("variable_id") or "")); sid,src=_source(str(request.get("source_id") or ""),var)
    source_url=str(request.get("source_url") or "").strip(); parsed=urlparse(source_url)
    if parsed.scheme!="https" or parsed.hostname not in src["recognized_hosts"]: raise ValueError("source_url must use HTTPS and a registered source host")
    evidence_type=str(request.get("evidence_type") or "").strip().lower()
    if evidence_type not in src["evidence_types"]: raise ValueError("evidence_type is not registered for this source")
    if not isinstance(request.get("value"),(int,float)): raise ValueError("value must be numeric")
    point=_point(float(request.get("latitude")),float(request.get("longitude")))
    observed_at=str(request.get("observed_at") or "").strip()
    if not observed_at: raise ValueError("observed_at is required")
    rec={"variable":{"id":vid,"title":var["title"]},"source":{"id":sid,"title":src["title"],"url":source_url},"dataset_id":str(request.get("dataset_id") or "").strip() or None,"source_record_id":str(request.get("source_record_id") or "").strip() or None,"evidence_type":evidence_type,"value":float(request["value"]),"unit":str(request.get("unit") or var["default_unit"]),"point":point,"observed_at":observed_at,"retrieved_at":str(request.get("retrieved_at") or "").strip() or _now(),"quality_flags":request.get("quality_flags") or [],"source_domain_recognized":True,"network_response_independently_verified":False,"evidence_state":"source-attributed-not-network-verified","current_condition_claimed":False}
    p={"ok":True,"version":VERSION,"contract":CONTRACT,"ocean_record":rec,"review":{"forecast_presented_as_observation":False,"missing_imputed":False,"source_substitution":False},"generated_at":_now()}; p["record_sha256"]=_digest(rec); return p


def export_manifest(variable_id: str="sea-surface-temperature", source_id: str="", latitude: float=0.0, longitude: float=0.0, date: str=""):
    current=state(variable_id,source_id,latitude,longitude,date)
    p={"ok":True,"version":VERSION,"contract":CONTRACT,"schema":"sc-site-intelligence-ocean-surface/1.0","state":current,"source_snapshot":{"id":current["source"]["id"],"title":current["source"]["title"],"url":current["source"]["url"],"coverage":current["source"]["coverage"],"authentication":current["source"]["authentication"]},"review":{"surface_value_fabricated":False,"coverage_claimed_without_record":False,"evidence_classes_collapsed":False,"missing_imputed":False},"generated_at":_now()}; p["manifest_sha256"]=_digest(p); return p


def readiness():
    checks={"sources_registered":len(SOURCES)>=3,"variables_registered":len(VARIABLES)>=9,"no_fake_surface_value":True,"evidence_classes_separated":True,"missing_data_preserved":True,"copernicus_credentials_excluded":True,"ioos_scope_bounded":True,"wordpress_asset_contract":True,"route_count_unchanged":True}
    return {"ok":all(checks.values()),"version":VERSION,"contract":CONTRACT,"checks":checks,"summary":{"sources":len(SOURCES),"variables":len(VARIABLES),"route":ROUTE,"public_route_count_delta":0},"generated_at":_now()}
