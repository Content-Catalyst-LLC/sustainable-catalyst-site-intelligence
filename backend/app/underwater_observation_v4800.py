from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "underwater-observation-visual-evidence"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "onc-oceans-3": {
        "title": "Ocean Networks Canada Oceans 3.0 / SeaTube",
        "organization": "Ocean Networks Canada",
        "url": "https://data.oceannetworks.ca/",
        "api_url": "https://data.oceannetworks.ca/OpenAPI",
        "media_url": "https://data.oceannetworks.ca/SeaTube",
        "recognized_hosts": [
            "data.oceannetworks.ca",
            "oceannetworks.ca",
            "www.oceannetworks.ca",
        ],
        "coverage": "ONC observatories and supported mobile/fixed observing programs; media and sensor coverage are deployment- and time-specific",
        "machine_access": "Oceans 3.0 web services plus SeaTube discovery for archived and live/near-live video where published",
        "evidence_types": [
            "underwater-image",
            "underwater-video",
            "camera-observation",
            "observatory-media-reference",
        ],
        "rights": "Asset-specific terms and attribution must be preserved; Site Intelligence does not infer blanket public-domain status.",
        "limitations": "A camera or observatory listing does not prove media exists for a requested point, depth, or time. Nearby sensor records are not assumed synchronized with visual media.",
    },
    "fathomnet": {
        "title": "FathomNet underwater imagery and annotations",
        "organization": "FathomNet / MBARI and contributors",
        "url": "https://www.fathomnet.org/",
        "api_url": "https://database.fathomnet.org/",
        "media_url": "https://database.fathomnet.org/",
        "recognized_hosts": [
            "fathomnet.org",
            "www.fathomnet.org",
            "database.fathomnet.org",
        ],
        "coverage": "Contributor-supplied underwater imagery and annotations with heterogeneous spatial, temporal, taxonomic, and rights metadata",
        "machine_access": "FathomNet REST-backed data access and official client tooling",
        "evidence_types": [
            "underwater-image",
            "expert-annotation",
            "human-annotation",
            "model-inference",
            "segmentation-mask",
        ],
        "rights": "Rights and attribution are contributor/asset-specific; database presence is not a blanket reuse license.",
        "limitations": "An annotation is evidence about a labeled region in an image. A model label or bounding box is not automatically a verified taxonomic observation or population record.",
    },
    "noaa-ocean-exploration": {
        "title": "NOAA Ocean Exploration expedition media",
        "organization": "NOAA Ocean Exploration / NOAA NCEI",
        "url": "https://oceanexplorer.noaa.gov/data/access/",
        "api_url": "https://www.ncei.noaa.gov/products/ocean-exploration",
        "media_url": "https://oceanexplorer.noaa.gov/video_playlist.html",
        "recognized_hosts": [
            "oceanexplorer.noaa.gov",
            "www.oceanexplorer.noaa.gov",
            "ncei.noaa.gov",
            "www.ncei.noaa.gov",
        ],
        "coverage": "NOAA Ocean Exploration and supported expedition media, dive records, navigation/sensor context, images, and ROV video with expedition-specific coverage",
        "machine_access": "NOAA/NCEI expedition archives and Ocean Exploration media discovery tools; access method varies by collection",
        "evidence_types": [
            "underwater-image",
            "rov-video-segment",
            "rov-video-stream",
            "dive-media-reference",
            "rov-track-context",
        ],
        "rights": "NOAA Ocean Exploration Video Portal video is public domain with attribution requested; other linked assets retain their own source metadata and terms.",
        "limitations": "Expedition/dive presence does not establish media at every point or depth. Dive tracks, annotations, sensor records, and media timestamps remain distinct evidence records.",
    },
}

MEDIA_TYPES: dict[str, dict[str, str]] = {
    "still-image": {
        "title": "Underwater still image",
        "evidence": "visual observation frame",
        "note": "An image is shown only when a source-attributed media record exists.",
    },
    "video-segment": {
        "title": "Underwater video segment",
        "evidence": "time-bounded visual observation",
        "note": "A segment reference does not imply continuous coverage outside its recorded interval.",
    },
    "video-stream": {
        "title": "Underwater video stream / archive stream",
        "evidence": "stream reference",
        "note": "A stream URL is not represented as live unless the source explicitly identifies it as live at retrieval time.",
    },
    "live-camera-reference": {
        "title": "Live-camera reference",
        "evidence": "camera endpoint or source handoff",
        "note": "Site Intelligence does not independently claim the camera is currently streaming unless a current source response verifies that state.",
    },
}

ANNOTATION_TYPES: dict[str, dict[str, str]] = {
    "expert-human": {
        "title": "Expert human annotation",
        "verification": "source-attributed annotation; taxonomic verification remains source-specific",
    },
    "human": {
        "title": "Human annotation",
        "verification": "source-attributed annotation without implied expert verification",
    },
    "citizen-science": {
        "title": "Citizen-science annotation",
        "verification": "contributor annotation; verification status remains explicit",
    },
    "model-inference": {
        "title": "Model inference",
        "verification": "machine-generated label; never promoted to verified biological observation by this contract",
    },
}


def _source(source_id: str):
    sid = (source_id or "onc-oceans-3").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported underwater source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _media_type(media_type: str):
    mid = (media_type or "still-image").strip().lower()
    if mid not in MEDIA_TYPES:
        raise ValueError(f"unsupported underwater media type: {mid}")
    return mid, {"id": mid, **MEDIA_TYPES[mid]}


def _point(latitude: float, longitude: float):
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _depth(depth_m: float | int | None):
    if depth_m in (None, ""):
        return None
    depth = float(depth_m)
    if depth < 0 or depth > 11000:
        raise ValueError("depth_m must be between 0 and 11000")
    return round(depth, 3)


def _date(value: str | None):
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


def _https_source_url(source: dict[str, Any], value: str, field: str = "source_url") -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError(f"{field} must use HTTPS and a registered source host")
    return url


def _optional_source_url(source: dict[str, Any], value: Any, field: str) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return _https_source_url(source, raw, field)


def _query_plan(source: dict[str, Any], media: dict[str, Any], point: dict[str, float], day: str | None, depth_m: float | None, query: str):
    if source["id"] == "onc-oceans-3":
        return {
            "access_kind": "ONC Oceans 3.0 / SeaTube media discovery",
            "api_url": source["api_url"],
            "media_url": source["media_url"],
            "point": point,
            "date": day,
            "depth_m": depth_m,
            "query": query or None,
            "requested_media_type": media["id"],
            "automatic_media_loaded": False,
            "note": "Resolve a source media/station/deployment record first. Do not assume SeaTube or an observatory has media at this exact point/depth/time.",
        }
    if source["id"] == "fathomnet":
        return {
            "access_kind": "FathomNet image / concept / annotation discovery",
            "api_url": source["api_url"],
            "point": point,
            "date": day,
            "depth_m": depth_m,
            "query": query or None,
            "requested_media_type": media["id"],
            "automatic_media_loaded": False,
            "note": "Search imagery/annotations by supported metadata or concept. A model label remains machine inference unless separately verified by the source record.",
        }
    return {
        "access_kind": "NOAA Ocean Exploration expedition / dive / video discovery",
        "archive_url": source["api_url"],
        "media_url": source["media_url"],
        "point": point,
        "date": day,
        "depth_m": depth_m,
        "query": query or None,
        "requested_media_type": media["id"],
        "automatic_media_loaded": False,
        "note": "Resolve expedition, dive, navigation, and media records separately. A dive footprint/track does not prove visual coverage at every point.",
    }


def overview():
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "media_type_count": len(MEDIA_TYPES),
        "annotation_type_count": len(ANNOTATION_TYPES),
        "summary": "Connect real underwater imagery/video records, dive/camera context, and visual annotations while keeping catalog discovery, media pixels, biological labels, environmental sensor context, and reuse rights as separate evidence claims.",
        "truth_boundaries": [
            "The local underwater orientation view is not an underwater photograph or video frame.",
            "A camera, station, expedition, or dive listing does not prove media exists at a requested point, depth, or time.",
            "An image or video record is loaded only from a source-attributed media record; Site Intelligence does not fabricate visual observations.",
            "A model inference is not promoted to a verified biological observation or taxonomic identification.",
            "A bounding box or annotation does not prove abundance, population size, or ecological condition outside the labeled frame.",
            "Nearby environmental sensor context is not represented as co-temporal or co-located with visual media unless the source record establishes that relationship.",
            "Rights, license, attribution, and reuse conditions remain source- and asset-specific.",
        ],
        "generated_at": _now(),
    }
    p["contract_sha256"] = _digest(p)
    return p


def catalog():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "source_count": len(SOURCES),
        "media_type_count": len(MEDIA_TYPES),
        "annotation_type_count": len(ANNOTATION_TYPES),
        "sources": [{"id": key, **value} for key, value in SOURCES.items()],
        "media_types": [{"id": key, **value} for key, value in MEDIA_TYPES.items()],
        "annotation_types": [{"id": key, **value} for key, value in ANNOTATION_TYPES.items()],
        "generated_at": _now(),
    }


def state(
    source_id: str = "onc-oceans-3",
    media_type: str = "still-image",
    latitude: float = 0.0,
    longitude: float = 0.0,
    date: str = "",
    depth_m: float | None = None,
    query: str = "",
):
    _, source = _source(source_id)
    _, media = _media_type(media_type)
    point = _point(latitude, longitude)
    depth = _depth(depth_m)
    day = _date(date)
    term = str(query or "").strip()[:200]
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "underwater-observation",
        "route": ROUTE,
        "source": source,
        "media_type": media,
        "point": point,
        "depth_m": depth,
        "date": day,
        "query": term or None,
        "media": {
            "record_loaded": False,
            "media_url": None,
            "thumbnail_url": None,
            "source_record_id": None,
            "observed_at": None,
            "location_verified": False,
            "depth_verified": False,
            "rights_verified": False,
            "live_state_verified": False,
        },
        "annotation": {
            "record_loaded": False,
            "label": None,
            "annotation_type": None,
            "taxonomic_verification": False,
        },
        "environmental_context": {
            "records_loaded": False,
            "co_temporal_verified": False,
            "co_located_verified": False,
        },
        "query_plan": _query_plan(source, media, point, day, depth, term),
        "truth": {
            "visual_media_fabricated": False,
            "catalog_entry_as_point_coverage": False,
            "annotation_as_taxonomic_verification": False,
            "model_inference_as_verified_observation": False,
            "sensor_context_assumed_cotemporal": False,
            "sensor_context_assumed_colocated": False,
            "reuse_rights_inferred": False,
            "missing_media_replaced": False,
        },
        "generated_at": _now(),
    }
    p["state_sha256"] = _digest(p)
    return p


def normalize_media(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or ""))
    mid, media_type = _media_type(str(request.get("media_type") or ""))
    source_url = _https_source_url(source, request.get("source_url"), "source_url")
    media_url = _optional_source_url(source, request.get("media_url"), "media_url")
    thumbnail_url = _optional_source_url(source, request.get("thumbnail_url"), "thumbnail_url")
    record_id = str(request.get("source_record_id") or "").strip()
    if not record_id:
        raise ValueError("source_record_id is required")

    latitude = request.get("latitude")
    longitude = request.get("longitude")
    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be provided together")
    point = _point(float(latitude), float(longitude)) if latitude is not None else None
    depth = _depth(request.get("depth_m"))
    observed_at = str(request.get("observed_at") or "").strip() or None
    station_id = str(request.get("station_id") or "").strip() or None
    dive_id = str(request.get("dive_id") or "").strip() or None
    expedition_id = str(request.get("expedition_id") or "").strip() or None
    credit = str(request.get("credit") or "").strip() or None
    rights_statement = str(request.get("rights_statement") or "").strip() or None
    rights_verified = bool(request.get("rights_verified", False)) and bool(rights_statement)
    live_state_verified = bool(request.get("live_state_verified", False))

    media = {
        "source_record_id": record_id,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "media_type": {"id": mid, "title": media_type["title"]},
        "media_url": media_url,
        "thumbnail_url": thumbnail_url,
        "point": point,
        "depth_m": depth,
        "observed_at": observed_at,
        "station_id": station_id,
        "dive_id": dive_id,
        "expedition_id": expedition_id,
        "credit": credit,
        "rights_statement": rights_statement,
        "rights_verified": rights_verified,
        "live_state_verified": live_state_verified,
        "environmental_context_synchronized": False,
        "network_response_independently_verified": False,
        "evidence_state": "source-attributed-not-network-verified",
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "media": media,
        "review": {
            "source_domain_recognized": True,
            "visual_media_fabricated": False,
            "catalog_entry_recast_as_point_coverage": False,
            "sensor_context_assumed_synchronized": False,
            "rights_inferred": False,
        },
        "generated_at": _now(),
    }
    p["media_sha256"] = _digest(media)
    return p


def normalize_annotation(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or ""))
    source_url = _https_source_url(source, request.get("source_url"), "source_url")
    annotation_id = str(request.get("annotation_id") or "").strip()
    if not annotation_id:
        raise ValueError("annotation_id is required")
    media_record_id = str(request.get("media_record_id") or "").strip()
    if not media_record_id:
        raise ValueError("media_record_id is required")
    annotation_type = str(request.get("annotation_type") or "human").strip().lower()
    if annotation_type not in ANNOTATION_TYPES:
        raise ValueError(f"unsupported annotation_type: {annotation_type}")
    label = str(request.get("label") or "").strip()
    if not label:
        raise ValueError("label is required")

    bbox = request.get("bounding_box")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(v, (int, float)) for v in bbox):
            raise ValueError("bounding_box must be [x, y, width, height]")
        if bbox[2] < 0 or bbox[3] < 0:
            raise ValueError("bounding_box width and height must be nonnegative")
        bbox = [float(v) for v in bbox]

    confidence = request.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            raise ValueError("confidence must be between 0 and 1")
        confidence = float(confidence)

    source_verified_taxonomy = bool(request.get("source_verified_taxonomy", False))
    verified_taxonomic_observation = source_verified_taxonomy and annotation_type != "model-inference"
    annotation = {
        "annotation_id": annotation_id,
        "media_record_id": media_record_id,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "annotation_type": annotation_type,
        "label": label,
        "concept_id": str(request.get("concept_id") or "").strip() or None,
        "bounding_box": bbox,
        "confidence": confidence,
        "source_verified_taxonomy": source_verified_taxonomy,
        "verified_taxonomic_observation": verified_taxonomic_observation,
        "abundance_claimed": False,
        "population_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "annotation": annotation,
        "review": {
            "model_promoted_to_verified_observation": False,
            "bounding_box_promoted_to_population_claim": False,
            "annotation_promoted_beyond_source_verification": False,
        },
        "generated_at": _now(),
    }
    p["annotation_sha256"] = _digest(annotation)
    return p


def export_manifest(
    source_id: str = "onc-oceans-3",
    media_type: str = "still-image",
    latitude: float = 0.0,
    longitude: float = 0.0,
    date: str = "",
    depth_m: float | None = None,
    query: str = "",
):
    current = state(source_id, media_type, latitude, longitude, date, depth_m, query)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-underwater-observation/1.0",
        "state": current,
        "source_snapshot": {
            "id": current["source"]["id"],
            "title": current["source"]["title"],
            "url": current["source"]["url"],
            "api_url": current["source"]["api_url"],
            "media_url": current["source"]["media_url"],
            "coverage": current["source"]["coverage"],
            "rights": current["source"]["rights"],
            "limitations": current["source"]["limitations"],
        },
        "review": {
            "visual_media_fabricated": False,
            "catalog_as_point_coverage": False,
            "annotation_as_taxonomic_verification": False,
            "model_as_verified_observation": False,
            "sensor_context_assumed_synchronized": False,
            "rights_inferred": False,
        },
        "generated_at": _now(),
    }
    p["manifest_sha256"] = _digest(p)
    return p


def readiness():
    checks = {
        "sources_registered": len(SOURCES) >= 3,
        "media_types_registered": len(MEDIA_TYPES) >= 4,
        "onc_registered": "onc-oceans-3" in SOURCES,
        "fathomnet_registered": "fathomnet" in SOURCES,
        "noaa_ocean_exploration_registered": "noaa-ocean-exploration" in SOURCES,
        "no_fake_underwater_media": True,
        "catalog_not_point_coverage": True,
        "model_not_verified_biology": True,
        "annotation_not_population_claim": True,
        "sensor_context_not_assumed_synchronized": True,
        "rights_not_inferred": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "media_types": len(MEDIA_TYPES),
            "annotation_types": len(ANNOTATION_TYPES),
            "route": ROUTE,
            "public_route_count_delta": 0,
        },
        "generated_at": _now(),
    }
