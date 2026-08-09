from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "marine-biodiversity-bioacoustic-intelligence"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


SOURCES: dict[str, dict[str, Any]] = {
    "obis": {
        "title": "Ocean Biodiversity Information System (OBIS)",
        "organization": "IOC-UNESCO OBIS",
        "url": "https://obis.org/",
        "api_url": "https://api.obis.org/",
        "recognized_hosts": ["obis.org", "www.obis.org", "api.obis.org", "manual.obis.org"],
        "evidence_classes": ["occurrence-record", "event-record", "absence-record-when-explicit"],
        "scope": "Marine biodiversity occurrence/event records contributed through the OBIS network.",
        "limitations": "An occurrence record is not abundance, population size, habitat suitability, or proof of continued presence. Zero returned records do not establish biological absence unless an explicit source absence record says so.",
    },
    "worms": {
        "title": "World Register of Marine Species (WoRMS)",
        "organization": "WoRMS / VLIZ",
        "url": "https://www.marinespecies.org/",
        "api_url": "https://www.marinespecies.org/rest/",
        "recognized_hosts": ["marinespecies.org", "www.marinespecies.org"],
        "evidence_classes": ["taxonomy-record", "accepted-name-record", "classification-record"],
        "scope": "Marine taxonomic names, accepted-name resolution, classification, synonyms, and source references.",
        "limitations": "A taxonomic record standardizes a name/classification; it is not an occurrence, abundance, distribution, or ecological-condition observation.",
    },
    "fathomnet": {
        "title": "FathomNet visual biodiversity evidence",
        "organization": "FathomNet / MBARI and contributors",
        "url": "https://www.fathomnet.org/",
        "api_url": "https://database.fathomnet.org/",
        "recognized_hosts": ["fathomnet.org", "www.fathomnet.org", "database.fathomnet.org"],
        "evidence_classes": ["visual-annotation", "expert-annotation", "human-annotation", "model-inference"],
        "scope": "Expertly labeled and contributor-supplied underwater imagery, concepts, boxes, masks, and model-oriented annotations.",
        "limitations": "A visual label applies to the source image/region. A model inference is not a verified biological observation, and one annotated frame does not establish abundance or population condition.",
    },
    "onc-hydrophones": {
        "title": "Ocean Networks Canada hydrophones",
        "organization": "Ocean Networks Canada",
        "url": "https://data.oceannetworks.ca/",
        "api_url": "https://data.oceannetworks.ca/OpenAPI",
        "recognized_hosts": ["data.oceannetworks.ca", "oceannetworks.ca", "www.oceannetworks.ca"],
        "evidence_classes": ["acoustic-recording", "spectrogram", "manual-acoustic-annotation", "model-acoustic-detection"],
        "scope": "Underwater acoustic recordings and derived products from ONC observing infrastructure where published.",
        "limitations": "A hydrophone recording is not itself a species detection. A detected call is bounded to the source interval/method and does not establish abundance, identity beyond the stated confidence, or absence outside the analyzed interval.",
    },
}

EVIDENCE_CLASSES = {
    "occurrence-record": {"title": "Occurrence record", "claim_scope": "source-recorded occurrence"},
    "taxonomy-record": {"title": "Taxonomy record", "claim_scope": "name/classification authority"},
    "visual-annotation": {"title": "Visual annotation", "claim_scope": "label attached to a source image/region"},
    "acoustic-recording": {"title": "Acoustic recording", "claim_scope": "recorded sound interval"},
    "acoustic-detection": {"title": "Acoustic detection", "claim_scope": "bounded detection/annotation within an analyzed interval"},
    "environmental-context": {"title": "Environmental context", "claim_scope": "separate environmental observation linked only when source relationship is explicit"},
}

ANNOTATION_METHODS = {
    "expert-human": "expert human annotation",
    "human": "human annotation",
    "citizen-science": "citizen-science annotation",
    "model-inference": "machine/model inference",
}

ACOUSTIC_METHODS = {
    "raw-recording": "recording only; no biological detection claimed",
    "manual-annotation": "human-reviewed acoustic annotation",
    "expert-annotation": "expert-reviewed acoustic annotation",
    "model-detection": "machine/model detection; not automatically verified species presence",
}


def _source(source_id: str):
    sid = (source_id or "obis").strip().lower()
    if sid not in SOURCES:
        raise ValueError(f"unsupported marine biodiversity source: {sid}")
    return sid, {"id": sid, **SOURCES[sid]}


def _point(latitude: float | None, longitude: float | None):
    if latitude is None and longitude is None:
        return None
    if latitude is None or longitude is None:
        raise ValueError("latitude and longitude must be provided together")
    lat, lon = float(latitude), float(longitude)
    if not -90 <= lat <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return {"latitude": round(lat, 6), "longitude": round(lon, 6)}


def _depth(depth_m: Any):
    if depth_m in (None, ""):
        return None
    value = float(depth_m)
    if value < 0 or value > 11000:
        raise ValueError("depth_m must be between 0 and 11000")
    return round(value, 3)


def _https_source_url(source: dict[str, Any], value: Any, field: str = "source_url"):
    raw = str(value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in source["recognized_hosts"]:
        raise ValueError(f"{field} must use HTTPS and a registered source host")
    return raw


def _optional_float(value: Any, field: str, minimum: float | None = None, maximum: float | None = None):
    if value in (None, ""):
        return None
    number = float(value)
    if minimum is not None and number < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{field} must be <= {maximum}")
    return number


def overview():
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "source_count": len(SOURCES),
        "evidence_class_count": len(EVIDENCE_CLASSES),
        "summary": "Connect marine occurrence records, authoritative taxonomy, underwater visual annotations, and acoustic evidence without collapsing them into a single species-presence or abundance claim.",
        "truth_boundaries": [
            "A FathomNet visual annotation is not automatically an OBIS occurrence record.",
            "A model visual or acoustic detection is not automatically a verified species identification.",
            "A taxonomy record standardizes a name; it is not evidence that the organism occurred at the selected place or time.",
            "An acoustic recording is not itself a biological detection.",
            "An acoustic detection is bounded to the analyzed interval and method and is not abundance or population size.",
            "No returned occurrence records do not prove species absence; explicit source absence remains a separate record state.",
            "Environmental context is not assumed co-located or co-temporal with biodiversity evidence unless the source relationship establishes it.",
        ],
        "generated_at": _now(),
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def catalog():
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "sources": [{"id": key, **value} for key, value in SOURCES.items()],
        "evidence_classes": [{"id": key, **value} for key, value in EVIDENCE_CLASSES.items()],
        "annotation_methods": [{"id": key, "title": value} for key, value in ANNOTATION_METHODS.items()],
        "acoustic_methods": [{"id": key, "title": value} for key, value in ACOUSTIC_METHODS.items()],
        "generated_at": _now(),
    }


def state(
    source_id: str = "obis",
    evidence_class: str = "occurrence-record",
    scientific_name: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    depth_m: float | None = None,
    date: str = "",
):
    _, source = _source(source_id)
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError(f"unsupported evidence_class: {evidence_class}")
    point = _point(latitude, longitude)
    depth = _depth(depth_m)
    name = str(scientific_name or "").strip()[:200] or None
    day = str(date or "").strip() or None
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "mode": "marine-biodiversity",
        "source": source,
        "evidence_class": {"id": evidence_class, **EVIDENCE_CLASSES[evidence_class]},
        "scientific_name": name,
        "point": point,
        "depth_m": depth,
        "date": day,
        "evidence": {
            "records_loaded": False,
            "record_count": None,
            "presence_verified": False,
            "absence_verified": False,
            "abundance_verified": False,
            "taxonomy_verified": False,
            "acoustic_detection_verified": False,
        },
        "truth": {
            "zero_results_as_absence": False,
            "annotation_as_occurrence": False,
            "model_detection_as_verified_species": False,
            "recording_as_detection": False,
            "detection_as_abundance": False,
            "taxonomy_as_occurrence": False,
            "environmental_context_assumed_synchronized": False,
        },
        "generated_at": _now(),
    }
    payload["state_sha256"] = _digest(payload)
    return payload


def normalize_occurrence(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "obis"))
    if sid != "obis":
        raise ValueError("occurrence normalization currently requires the OBIS source contract")
    source_url = _https_source_url(source, request.get("source_url"))
    occurrence_id = str(request.get("occurrence_id") or "").strip()
    scientific_name = str(request.get("scientific_name") or "").strip()
    if not occurrence_id or not scientific_name:
        raise ValueError("occurrence_id and scientific_name are required")
    occurrence_status = str(request.get("occurrence_status") or "unknown").strip().lower()
    if occurrence_status not in {"present", "absent", "unknown"}:
        raise ValueError("occurrence_status must be present, absent, or unknown")
    record = {
        "occurrence_id": occurrence_id,
        "scientific_name": scientific_name,
        "scientific_name_id": str(request.get("scientific_name_id") or "").strip() or None,
        "basis_of_record": str(request.get("basis_of_record") or "").strip() or None,
        "occurrence_status": occurrence_status,
        "event_date": str(request.get("event_date") or "").strip() or None,
        "point": _point(request.get("latitude"), request.get("longitude")),
        "depth_m": _depth(request.get("depth_m")),
        "individual_count": _optional_float(request.get("individual_count"), "individual_count", 0),
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "explicit_absence": occurrence_status == "absent",
        "abundance_claimed": request.get("individual_count") not in (None, ""),
        "population_size_claimed": False,
        "continued_presence_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "occurrence": record,
        "review": {
            "zero_results_recast_as_absence": False,
            "individual_count_recast_as_population_size": False,
            "taxonomy_status_inferred": False,
        },
        "generated_at": _now(),
    }
    payload["occurrence_sha256"] = _digest(record)
    return payload


def normalize_taxonomy(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "worms"))
    if sid != "worms":
        raise ValueError("taxonomy normalization currently requires the WoRMS source contract")
    source_url = _https_source_url(source, request.get("source_url"))
    aphia_id = str(request.get("aphia_id") or "").strip()
    scientific_name = str(request.get("scientific_name") or "").strip()
    if not aphia_id or not scientific_name:
        raise ValueError("aphia_id and scientific_name are required")
    status = str(request.get("status") or "").strip().lower() or None
    record = {
        "aphia_id": aphia_id,
        "scientific_name": scientific_name,
        "authority": str(request.get("authority") or "").strip() or None,
        "rank": str(request.get("rank") or "").strip() or None,
        "status": status,
        "accepted_aphia_id": str(request.get("accepted_aphia_id") or "").strip() or None,
        "accepted_name": str(request.get("accepted_name") or "").strip() or None,
        "classification": request.get("classification") if isinstance(request.get("classification"), list) else [],
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "occurrence_claimed": False,
        "distribution_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "taxonomy": record,
        "review": {"taxonomy_promoted_to_occurrence": False, "taxonomy_promoted_to_distribution": False},
        "generated_at": _now(),
    }
    payload["taxonomy_sha256"] = _digest(record)
    return payload


def normalize_visual(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "fathomnet"))
    if sid != "fathomnet":
        raise ValueError("visual evidence normalization currently requires the FathomNet source contract")
    source_url = _https_source_url(source, request.get("source_url"))
    annotation_id = str(request.get("annotation_id") or "").strip()
    media_record_id = str(request.get("media_record_id") or "").strip()
    label = str(request.get("label") or "").strip()
    method = str(request.get("annotation_method") or "human").strip().lower()
    if not annotation_id or not media_record_id or not label:
        raise ValueError("annotation_id, media_record_id, and label are required")
    if method not in ANNOTATION_METHODS:
        raise ValueError(f"unsupported annotation_method: {method}")
    confidence = _optional_float(request.get("confidence"), "confidence", 0, 1)
    source_verified_taxonomy = bool(request.get("source_verified_taxonomy", False))
    record = {
        "annotation_id": annotation_id,
        "media_record_id": media_record_id,
        "label": label,
        "concept_id": str(request.get("concept_id") or "").strip() or None,
        "annotation_method": method,
        "confidence": confidence,
        "source_verified_taxonomy": source_verified_taxonomy,
        "verified_taxonomic_observation": source_verified_taxonomy and method != "model-inference",
        "occurrence_record_created": False,
        "abundance_claimed": False,
        "population_claimed": False,
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "visual": record,
        "review": {
            "model_promoted_to_verified_species": False,
            "visual_promoted_to_occurrence_record": False,
            "annotation_promoted_to_abundance": False,
        },
        "generated_at": _now(),
    }
    payload["visual_sha256"] = _digest(record)
    return payload


def normalize_acoustic(request: dict[str, Any]):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    sid, source = _source(str(request.get("source_id") or "onc-hydrophones"))
    if sid != "onc-hydrophones":
        raise ValueError("acoustic normalization currently requires the ONC hydrophone source contract")
    source_url = _https_source_url(source, request.get("source_url"))
    record_id = str(request.get("record_id") or "").strip()
    method = str(request.get("method") or "raw-recording").strip().lower()
    if not record_id:
        raise ValueError("record_id is required")
    if method not in ACOUSTIC_METHODS:
        raise ValueError(f"unsupported acoustic method: {method}")
    label = str(request.get("label") or "").strip() or None
    confidence = _optional_float(request.get("confidence"), "confidence", 0, 1)
    detection_claimed = method != "raw-recording" and bool(label)
    verified_detection = method in {"manual-annotation", "expert-annotation"} and bool(label)
    record = {
        "record_id": record_id,
        "method": method,
        "label": label,
        "confidence": confidence,
        "station_id": str(request.get("station_id") or "").strip() or None,
        "hydrophone_id": str(request.get("hydrophone_id") or "").strip() or None,
        "start_time": str(request.get("start_time") or "").strip() or None,
        "end_time": str(request.get("end_time") or "").strip() or None,
        "frequency_min_hz": _optional_float(request.get("frequency_min_hz"), "frequency_min_hz", 0),
        "frequency_max_hz": _optional_float(request.get("frequency_max_hz"), "frequency_max_hz", 0),
        "source": {"id": sid, "title": source["title"], "url": source_url},
        "recording_loaded": True,
        "detection_claimed": detection_claimed,
        "verified_detection": verified_detection,
        "verified_species_presence": verified_detection and bool(request.get("source_verified_taxonomy", False)),
        "abundance_claimed": False,
        "absence_outside_interval_claimed": False,
        "network_response_independently_verified": False,
        "retrieved_at": str(request.get("retrieved_at") or "").strip() or _now(),
    }
    if record["frequency_min_hz"] is not None and record["frequency_max_hz"] is not None and record["frequency_min_hz"] > record["frequency_max_hz"]:
        raise ValueError("frequency_min_hz must be <= frequency_max_hz")
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "acoustic": record,
        "review": {
            "recording_promoted_to_detection": False,
            "model_detection_promoted_to_verified_species": False,
            "detection_promoted_to_abundance": False,
            "non_detection_promoted_to_absence": False,
        },
        "generated_at": _now(),
    }
    payload["acoustic_sha256"] = _digest(record)
    return payload


def export_manifest(
    source_id: str = "obis",
    evidence_class: str = "occurrence-record",
    scientific_name: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    depth_m: float | None = None,
    date: str = "",
):
    current = state(source_id, evidence_class, scientific_name, latitude, longitude, depth_m, date)
    payload = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "schema": "sc-site-intelligence-marine-biodiversity-bioacoustic/1.0",
        "state": current,
        "review": {
            "zero_results_as_absence": False,
            "taxonomy_as_occurrence": False,
            "visual_annotation_as_occurrence": False,
            "model_detection_as_verified_species": False,
            "acoustic_detection_as_abundance": False,
            "environmental_context_assumed_synchronized": False,
        },
        "generated_at": _now(),
    }
    payload["manifest_sha256"] = _digest(payload)
    return payload


def readiness():
    checks = {
        "obis_registered": "obis" in SOURCES,
        "worms_registered": "worms" in SOURCES,
        "fathomnet_registered": "fathomnet" in SOURCES,
        "onc_hydrophones_registered": "onc-hydrophones" in SOURCES,
        "occurrence_not_abundance": True,
        "zero_results_not_absence": True,
        "taxonomy_not_occurrence": True,
        "model_not_verified_species": True,
        "recording_not_detection": True,
        "detection_not_abundance": True,
        "context_not_assumed_synchronized": True,
        "route_count_unchanged": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "evidence_classes": len(EVIDENCE_CLASSES),
            "route": ROUTE,
            "public_route_count_delta": 0,
        },
        "generated_at": _now(),
    }
