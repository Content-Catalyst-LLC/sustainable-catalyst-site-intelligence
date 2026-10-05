from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .version import APP_VERSION

EVIDENCE_OBJECT_SCHEMA = "sc-site-intelligence-spatial-evidence-object/2.0"
LAYER_REGISTRY_SCHEMA = "sc-site-intelligence-spatial-layer-registry/2.0"
REGISTRY_CONTRACT_VERSION = "1.0.0"
DEFAULT_CRS = "EPSG:4326"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "spatial_layer_registry_v4460.json"
ALLOWED_GEOMETRY_TYPES = {
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection", "RasterFootprint"
}
_SAFE_ID = re.compile(r"[^a-zA-Z0-9_.:-]+")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _safe_id(value: Any, fallback: str) -> str:
    cleaned = _SAFE_ID.sub("-", str(value or "").strip()).strip("-.")
    return (cleaned or fallback)[:160]


def _iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 datetime: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _walk_positions(value: Any):
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value[:2]):
            lon, lat = float(value[0]), float(value[1])
            if not -180 <= lon <= 180 or not -90 <= lat <= 90:
                raise ValueError("Geometry coordinates must use WGS84 longitude [-180,180] and latitude [-90,90].")
            yield lon, lat
        else:
            for item in value:
                yield from _walk_positions(item)


def _normalize_geometry(value: Any) -> tuple[dict[str, Any] | None, list[float] | None]:
    if value in (None, {}):
        return None, None
    if not isinstance(value, dict):
        raise ValueError("geometry must be a GeoJSON object or null")
    geometry = deepcopy(value)
    kind = str(geometry.get("type") or "").strip()
    if kind not in ALLOWED_GEOMETRY_TYPES:
        raise ValueError(f"Unsupported geometry type: {kind or 'missing'}")
    if kind == "RasterFootprint":
        coords = geometry.get("coordinates")
    elif kind == "GeometryCollection":
        positions=[]
        for child in geometry.get("geometries") or []:
            _, bbox = _normalize_geometry(child)
            if bbox:
                positions.extend([(bbox[0],bbox[1]),(bbox[2],bbox[3])])
        if not positions:
            raise ValueError("GeometryCollection contains no valid positions")
        lons=[p[0] for p in positions]; lats=[p[1] for p in positions]
        return geometry,[min(lons),min(lats),max(lons),max(lats)]
    else:
        coords = geometry.get("coordinates")
    positions=list(_walk_positions(coords))
    if not positions:
        raise ValueError("geometry contains no valid positions")
    lons=[p[0] for p in positions]; lats=[p[1] for p in positions]
    return geometry,[min(lons),min(lats),max(lons),max(lats)]


def load_layer_registry() -> dict[str, Any]:
    payload=json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != LAYER_REGISTRY_SCHEMA:
        raise ValueError("Spatial layer registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Spatial layer registry version does not match application version")
    layers=payload.get("layers") or []
    ids=[item.get("layer_id") for item in layers]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("Spatial layer registry contains missing or duplicate layer IDs")
    return payload


def _layer_map() -> dict[str, dict[str, Any]]:
    return {item["layer_id"]: item for item in load_layer_registry()["layers"]}


def registry_manifest() -> dict[str, Any]:
    registry=load_layer_registry()
    layers=registry["layers"]
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": REGISTRY_CONTRACT_VERSION,
        "schema": registry["schema"],
        "evidence_object_schema": EVIDENCE_OBJECT_SCHEMA,
        "coordinate_reference_system": DEFAULT_CRS,
        "layer_count": len(layers),
        "domain_count": len({item["domain"] for item in layers}),
        "capability_count": len({item["capability_id"] for item in layers}),
        "geometry_types": sorted({kind for item in layers for kind in item["geometry_types"]}),
        "legacy_compatibility": registry.get("legacy_compatibility", {}),
        "principles": registry.get("principles", []),
        "endpoints": {
            "layers": "/public/spatial-evidence/layers",
            "domains": "/public/spatial-evidence/domains",
            "object_schema": "/public/spatial-evidence/object-schema",
            "normalize": "/public/spatial-evidence/objects/normalize",
            "validate": "/public/spatial-evidence/objects/validate",
            "compatibility": "/public/spatial-evidence/compatibility",
        },
    }


def list_layers(*, domain: str | None = None, capability_id: str | None = None, geometry_type: str | None = None, q: str | None = None) -> dict[str, Any]:
    rows=[deepcopy(item) for item in load_layer_registry()["layers"]]
    if domain:
        rows=[item for item in rows if item["domain"] == domain]
    if capability_id:
        rows=[item for item in rows if item["capability_id"] == capability_id]
    if geometry_type:
        rows=[item for item in rows if geometry_type in item.get("geometry_types", [])]
    if q:
        needle=q.strip().lower()
        rows=[item for item in rows if needle in " ".join([item.get("layer_id",""),item.get("title",""),item.get("description",""),*item.get("tags",[])]).lower()]
    return {"ok":True,"version":APP_VERSION,"schema":LAYER_REGISTRY_SCHEMA,"count":len(rows),"layers":rows}


def layer_detail(layer_id: str) -> dict[str, Any] | None:
    row=_layer_map().get(layer_id)
    if row is None:
        return None
    return {"ok":True,"version":APP_VERSION,"schema":LAYER_REGISTRY_SCHEMA,"layer":deepcopy(row)}


def domain_manifest() -> dict[str, Any]:
    rows=load_layer_registry()["layers"]
    domains=[]
    for domain in sorted({item["domain"] for item in rows}):
        items=[item for item in rows if item["domain"] == domain]
        domains.append({
            "domain":domain,
            "layer_count":len(items),
            "layer_ids":[item["layer_id"] for item in items],
            "capability_ids":sorted({item["capability_id"] for item in items}),
        })
    return {"ok":True,"version":APP_VERSION,"count":len(domains),"domains":domains}


def object_schema_contract() -> dict[str, Any]:
    return {
        "ok":True,
        "version":APP_VERSION,
        "schema":EVIDENCE_OBJECT_SCHEMA,
        "contract_version":REGISTRY_CONTRACT_VERSION,
        "required":["layer_id","geometry","source"],
        "fields":{
            "object_id":"Stable caller-supplied ID or deterministic content-derived ID.",
            "layer_id":"Registered v4.46 spatial layer identifier.",
            "domain":"Derived from the layer registry; caller mismatch is rejected.",
            "geometry":"WGS84 GeoJSON geometry or RasterFootprint.",
            "bbox":"Derived WGS84 [west,south,east,north] bounding box.",
            "observed_at":"Optional normalized UTC observation timestamp.",
            "valid_time":"Optional start/end validity interval.",
            "properties":"Source-domain attributes; no silent imputation.",
            "source":"Source identity, record identifier, license and retrieval context.",
            "provenance":"Transformation lineage, source CRS and derivation metadata.",
            "quality":"Spatial/temporal resolution and source-defined quality signals.",
            "visibility":"public, institutional, restricted, or private.",
            "content_digest":"SHA-256 digest over canonical normalized content.",
        },
        "allowed_geometry_types":sorted(ALLOWED_GEOMETRY_TYPES),
        "coordinate_reference_system":DEFAULT_CRS,
        "principles":["translation-and-transformation-are-derived-representations","no-silent-imputation","source-identity-preserved","visibility-does-not-change-source-provenance"],
    }


def normalize_evidence_object(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Spatial evidence object must be a JSON object")
    layer_id=_safe_id(request.get("layer_id"), "")
    layer=_layer_map().get(layer_id)
    if layer is None:
        raise ValueError(f"Unknown spatial layer_id: {layer_id or 'missing'}")
    supplied_domain=str(request.get("domain") or "").strip()
    if supplied_domain and supplied_domain != layer["domain"]:
        raise ValueError(f"domain must match layer registry domain: {layer['domain']}")
    geometry,bbox=_normalize_geometry(request.get("geometry"))
    if geometry is None:
        raise ValueError("geometry is required")
    if geometry.get("type") not in set(layer.get("geometry_types") or []):
        raise ValueError(f"Geometry type {geometry.get('type')} is not registered for layer {layer_id}")
    source=request.get("source")
    if not isinstance(source, dict) or not str(source.get("source_id") or source.get("authority") or "").strip():
        raise ValueError("source must identify source_id or authority")
    valid=request.get("valid_time") if isinstance(request.get("valid_time"),dict) else {}
    normalized={
        "schema":EVIDENCE_OBJECT_SCHEMA,
        "version":APP_VERSION,
        "object_id":None,
        "layer_id":layer_id,
        "domain":layer["domain"],
        "capability_id":layer["capability_id"],
        "geometry":geometry,
        "bbox":bbox,
        "crs":DEFAULT_CRS,
        "observed_at":_iso(request.get("observed_at")),
        "valid_time":{"start":_iso(valid.get("start")),"end":_iso(valid.get("end"))},
        "properties":deepcopy(request.get("properties") if isinstance(request.get("properties"),dict) else {}),
        "source":{
            "source_id":str(source.get("source_id") or source.get("authority") or "").strip(),
            "authority":str(source.get("authority") or source.get("source_id") or "").strip(),
            "record_id":str(source.get("record_id") or "").strip() or None,
            "url":str(source.get("url") or "").strip() or None,
            "license":str(source.get("license") or "").strip() or None,
            "retrieved_at":_iso(source.get("retrieved_at")),
        },
        "provenance":deepcopy(request.get("provenance") if isinstance(request.get("provenance"),dict) else {}),
        "quality":deepcopy(request.get("quality") if isinstance(request.get("quality"),dict) else {}),
        "visibility":str(request.get("visibility") or "public").strip().lower(),
    }
    if normalized["visibility"] not in {"public","institutional","restricted","private"}:
        raise ValueError("visibility must be public, institutional, restricted, or private")
    transformations=normalized["provenance"].get("transformations")
    if transformations is None:
        normalized["provenance"]["transformations"]=[]
    elif not isinstance(transformations,list):
        raise ValueError("provenance.transformations must be a list")
    normalized["provenance"].setdefault("source_crs", request.get("source_crs") or DEFAULT_CRS)
    normalized["provenance"].setdefault("normalization_contract", REGISTRY_CONTRACT_VERSION)
    basis=deepcopy(normalized)
    basis.pop("object_id",None)
    digest=_digest(basis)
    normalized["object_id"]=_safe_id(request.get("object_id"), f"se-{digest[:24]}")
    normalized["content_digest"]="sha256:"+_digest({k:v for k,v in normalized.items() if k != "content_digest"})
    return normalized


def validate_evidence_object(request: dict[str, Any]) -> dict[str, Any]:
    try:
        normalized=normalize_evidence_object(request)
    except (TypeError,ValueError) as exc:
        return {"ok":False,"version":APP_VERSION,"schema":EVIDENCE_OBJECT_SCHEMA,"valid":False,"errors":[str(exc)]}
    return {"ok":True,"version":APP_VERSION,"schema":EVIDENCE_OBJECT_SCHEMA,"valid":True,"errors":[],"object_id":normalized["object_id"],"layer_id":normalized["layer_id"],"content_digest":normalized["content_digest"]}


def compatibility_contract() -> dict[str, Any]:
    registry=load_layer_registry()
    return {
        "ok":True,
        "version":APP_VERSION,
        "contract_version":REGISTRY_CONTRACT_VERSION,
        "legacy_spatial_studio":{
            "status":"preserved",
            "summary":"/public/spatial",
            "layers":"/public/spatial/layers",
            "analysis_routes":"unchanged",
            "catalog_schema":registry["legacy_compatibility"]["catalog_schema"],
        },
        "v4_46":{
            "registry":"/public/spatial-evidence/registry",
            "layers":"/public/spatial-evidence/layers",
            "object_schema":"/public/spatial-evidence/object-schema",
            "normalization":"/public/spatial-evidence/objects/normalize",
        },
        "migration_rule":"Existing spatial datasets and analysis routes remain valid; v4.46 adds a canonical cross-domain interchange object and registry without rewriting source records.",
    }
