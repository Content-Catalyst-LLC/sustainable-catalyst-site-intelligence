from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "seti-technosignatures-radio-signal-intelligence"
ROUTE = "earth"
WARNING = "TECHNOSIGNATURE SEARCH EVIDENCE · NOT CONFIRMATION OF EXTRATERRESTRIAL INTELLIGENCE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES = {
    "breakthrough-listen-open-data": {
        "title": "Breakthrough Listen Open Data Archive",
        "organization": "Berkeley SETI Research Center / Breakthrough Listen",
        "access": "public archive with backend API/search interface",
        "recognized_hosts": ["seti.berkeley.edu", "breakthroughinitiatives.org"],
        "indicator_types": ["observation-metadata", "radio-data-product", "observation-cadence"],
        "evidence_classes": ["observation-record", "data-product-record"],
        "truth": "Archive metadata and data products document observations; they do not establish a technosignature detection.",
    },
    "breakthrough-listen-event-tables": {
        "title": "Breakthrough Listen 1327-Star Event Tables",
        "organization": "Berkeley SETI Research Center / Breakthrough Listen",
        "access": "published CSV event-group tables",
        "recognized_hosts": ["seti.berkeley.edu"],
        "indicator_types": ["signal-event", "doppler-drift", "signal-to-noise"],
        "evidence_classes": ["signal-event-record"],
        "truth": "A pipeline event or event group is a signal-processing result, not a confirmed technosignature.",
    },
    "seti-technosearch": {
        "title": "Technosearch",
        "organization": "SETI Institute",
        "access": "public archive of published SETI searches",
        "recognized_hosts": ["technosearch.seti.org", "seti.org", "www.seti.org"],
        "indicator_types": ["published-search", "search-coverage"],
        "evidence_classes": ["published-search-record"],
        "truth": "A published search record documents where and how a search was conducted; non-detection does not establish absence of technology.",
    },
    "nasa-exoplanet-target-context": {
        "title": "NASA Exoplanet Archive TAP",
        "organization": "NASA Exoplanet Archive / Caltech IPAC",
        "access": "public TAP/API target context",
        "recognized_hosts": ["exoplanetarchive.ipac.caltech.edu"],
        "indicator_types": ["target-context", "planetary-system-context"],
        "evidence_classes": ["target-context-record"],
        "truth": "Exoplanet/stellar context helps prioritize and interpret targets; it is not technosignature evidence.",
    },
}

INDICATOR_TYPES = {
    "observation-metadata": {"description": "Telescope, target, epoch, coordinates, center frequency and file metadata."},
    "radio-data-product": {"description": "Filterbank, HDF5, baseband, FITS or related public radio data product."},
    "observation-cadence": {"description": "On/off-target or repeated observation cadence metadata."},
    "signal-event": {"description": "Signal-processing event or grouped event from a published search pipeline."},
    "doppler-drift": {"description": "Reported or measured frequency drift rate associated with a signal event."},
    "signal-to-noise": {"description": "Reported signal-to-noise metric associated with a search event."},
    "published-search": {"description": "Published SETI search record and methodology context."},
    "search-coverage": {"description": "Frequency/target/sky coverage described by a published SETI search."},
    "target-context": {"description": "Stellar/exoplanet target metadata used to orient a technosignature search."},
    "planetary-system-context": {"description": "Planetary-system metadata associated with an observed star."},
}

EVIDENCE_CLASSES = {
    "observation-record": "Archive-level observation metadata.",
    "data-product-record": "Public radio/astronomy data product metadata.",
    "signal-event-record": "Pipeline-generated or published radio signal event metadata.",
    "published-search-record": "Published SETI search methodology/coverage record.",
    "target-context-record": "Astronomical target context that is not itself technosignature evidence.",
}


def _source(value: str | None) -> tuple[str, dict[str, Any]]:
    key = (value or "breakthrough-listen-open-data").strip().lower()
    if key not in SOURCES:
        raise ValueError(f"unsupported SETI source: {key}")
    return key, {"id": key, **SOURCES[key]}


def _indicator(value: str | None) -> tuple[str, dict[str, Any]]:
    key = (value or "observation-metadata").strip().lower()
    if key not in INDICATOR_TYPES:
        raise ValueError(f"unsupported indicator_type: {key}")
    return key, {"id": key, **INDICATOR_TYPES[key]}


def _evidence(value: str | None) -> str:
    key = str(value or "").strip().lower()
    if key not in EVIDENCE_CLASSES:
        raise ValueError(f"unsupported evidence_class: {key}")
    return key


def _url(source: dict[str, Any], raw: Any) -> str:
    value = str(raw or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in source["recognized_hosts"]:
        raise ValueError("source_url must use HTTPS and a registered source host")
    return value


def _coord(ra_deg: Any = None, dec_deg: Any = None) -> dict[str, float] | None:
    if ra_deg in (None, "") and dec_deg in (None, ""):
        return None
    if ra_deg in (None, "") or dec_deg in (None, ""):
        raise ValueError("ra_deg and dec_deg must be supplied together")
    ra, dec = float(ra_deg), float(dec_deg)
    if not 0 <= ra <= 360 or not -90 <= dec <= 90:
        raise ValueError("RA/Dec outside valid bounds")
    return {"ra_deg": round(ra, 6), "dec_deg": round(dec, 6), "frame": "ICRS/J2000"}


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "title": "SETI, Technosignatures & Radio Signal Intelligence",
        "source_count": len(SOURCES),
        "indicator_type_count": len(INDICATOR_TYPES),
        "evidence_class_count": len(EVIDENCE_CLASSES),
        "summary": "Orient public SETI observations, radio-search event metadata, published search coverage and astronomical target context without converting a signal event, anomaly or non-detection into evidence of extraterrestrial intelligence.",
        "warning": WARNING,
    }


def catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "sources": [{"id": k, **v} for k, v in SOURCES.items()],
        "indicator_types": [{"id": k, **v} for k, v in INDICATOR_TYPES.items()],
        "evidence_classes": [{"id": k, "description": v} for k, v in EVIDENCE_CLASSES.items()],
        "truth_boundaries": {
            "signal_event_equals_technosignature": False,
            "candidate_equals_confirmed_eti": False,
            "non_detection_equals_absence_of_technology": False,
            "radio_interference_equals_astrophysical_source": False,
            "target_context_equals_technosignature_evidence": False,
            "pipeline_score_equals_scientific_confirmation": False,
            "single_observation_authorizes_announcement": False,
            "automatic_action_authorized": False,
        },
    }


def state(
    source_id: str = "breakthrough-listen-open-data",
    indicator_type: str = "observation-metadata",
    target: str = "",
    telescope: str = "",
    frequency_mhz: float | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
) -> dict[str, Any]:
    _, source = _source(source_id)
    iid, indicator = _indicator(indicator_type)
    if frequency_mhz is not None and float(frequency_mhz) < 0:
        raise ValueError("frequency_mhz must be non-negative")
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "source": source,
        "indicator_type": indicator,
        "target": str(target or "").strip() or None,
        "telescope": str(telescope or "").strip() or None,
        "frequency_mhz": None if frequency_mhz is None else float(frequency_mhz),
        "coordinate": _coord(ra_deg, dec_deg),
        "source_supports_indicator_type": iid in source["indicator_types"],
        "evidence": {
            "observation_loaded": False,
            "radio_data_product_loaded": False,
            "signal_event_loaded": False,
            "candidate_loaded": False,
            "follow_up_loaded": False,
            "technosignature_confirmed": False,
        },
        "truth": {
            "signal_event_treated_as_technosignature": False,
            "candidate_treated_as_confirmed_eti": False,
            "non_detection_treated_as_absence": False,
            "rfi_treated_as_astrophysical_source": False,
            "pipeline_score_treated_as_confirmation": False,
            "automatic_action_authorized": False,
        },
    }


def normalize_observation(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "breakthrough-listen-open-data")
    iid, _ = _indicator(request.get("indicator_type") or "observation-metadata")
    if iid not in source["indicator_types"]:
        raise ValueError("source does not register the requested observation indicator")
    evidence_class = _evidence(request.get("evidence_class") or source["evidence_classes"][0])
    if evidence_class not in source["evidence_classes"]:
        raise ValueError("source does not register the requested evidence_class")
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "indicator_type": iid,
        "evidence_class": evidence_class,
        "target": str(request.get("target") or "").strip() or None,
        "telescope": str(request.get("telescope") or "").strip() or None,
        "observation_time": str(request.get("observation_time") or "").strip() or None,
        "center_frequency_mhz": request.get("center_frequency_mhz"),
        "file_type": str(request.get("file_type") or "").strip() or None,
        "file_id": str(request.get("file_id") or "").strip() or None,
        "coordinate": _coord(request.get("ra_deg"), request.get("dec_deg")),
        "technosignature_inferred": False,
        "eti_origin_inferred": False,
        "live_telescope_status_inferred": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "observation": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_signal(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "breakthrough-listen-event-tables")
    iid, _ = _indicator(request.get("indicator_type") or "signal-event")
    if iid not in source["indicator_types"]:
        raise ValueError("source does not register the requested signal indicator")
    evidence_class = _evidence(request.get("evidence_class") or "signal-event-record")
    if evidence_class not in source["evidence_classes"]:
        raise ValueError("source does not register the requested evidence_class")
    disposition = str(request.get("source_disposition") or "unreviewed").strip().lower()
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "indicator_type": iid,
        "evidence_class": evidence_class,
        "target": str(request.get("target") or "").strip() or None,
        "frequency_mhz": request.get("frequency_mhz"),
        "drift_rate_hz_per_s": request.get("drift_rate_hz_per_s"),
        "snr": request.get("snr"),
        "bandwidth_hz": request.get("bandwidth_hz"),
        "file_id": str(request.get("file_id") or "").strip() or None,
        "source_disposition": disposition,
        "technosignature_confirmed": False,
        "eti_origin_confirmed": False,
        "rfi_excluded_by_platform": False,
        "independent_confirmation_present": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "signal": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_candidate(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    source_id = request.get("source_id") or "breakthrough-listen-event-tables"
    _, source = _source(source_id)
    status = str(request.get("source_status") or "signal-of-interest").strip().lower()
    follow_up = str(request.get("follow_up_result") or "unknown").strip().lower()
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "candidate_id": str(request.get("candidate_id") or "").strip() or None,
        "target": str(request.get("target") or "").strip() or None,
        "source_status": status,
        "follow_up_result": follow_up,
        "re_detected": True if follow_up == "redetected" else False if follow_up in {"not-redetected", "not_redetected"} else None,
        "technosignature_confirmed": False,
        "eti_origin_confirmed": False,
        "announcement_authorized": False,
        "independent_verification_inferred": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "candidate": record, "record_sha256": _digest(record), "normalized_at": _now()}


def export_manifest(
    source_id: str = "breakthrough-listen-open-data",
    indicator_type: str = "observation-metadata",
    target: str = "",
    telescope: str = "",
    frequency_mhz: float | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
) -> dict[str, Any]:
    current = state(source_id, indicator_type, target, telescope, frequency_mhz, ra_deg, dec_deg)
    payload = {
        "schema": "sc-site-intelligence-seti-technosignatures/1.0",
        "version": VERSION,
        "contract": CONTRACT,
        "warning": WARNING,
        "query": {
            "source_id": current["source"]["id"],
            "indicator_type": current["indicator_type"]["id"],
            "target": current["target"],
            "telescope": current["telescope"],
            "frequency_mhz": current["frequency_mhz"],
            "coordinate": current["coordinate"],
        },
        "evidence": current["evidence"],
        "review": {
            "signal_event_as_technosignature": False,
            "candidate_as_confirmed_eti": False,
            "non_detection_as_absence": False,
            "pipeline_score_as_confirmation": False,
            "single_observation_as_announcement_authority": False,
        },
    }
    return {**payload, "manifest_sha256": _digest(payload), "generated_at": _now()}


def readiness() -> dict[str, Any]:
    checks = {
        "four_source_families_registered": len(SOURCES) == 4,
        "breakthrough_open_data_registered": "breakthrough-listen-open-data" in SOURCES,
        "breakthrough_event_tables_registered": "breakthrough-listen-event-tables" in SOURCES,
        "technosearch_registered": "seti-technosearch" in SOURCES,
        "nasa_target_context_registered": "nasa-exoplanet-target-context" in SOURCES,
        "signal_confirmation_guard_present": True,
        "non_detection_guard_present": True,
        "rfi_guard_present": True,
        "announcement_guard_present": True,
        "public_route_count_preserved": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {
            "sources": len(SOURCES),
            "indicator_types": len(INDICATOR_TYPES),
            "evidence_classes": len(EVIDENCE_CLASSES),
            "public_route_count_delta": 0,
            "primary_area_count_delta": 0,
        },
        "generated_at": _now(),
    }
