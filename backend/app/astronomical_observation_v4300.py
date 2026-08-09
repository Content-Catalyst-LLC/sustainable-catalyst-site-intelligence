from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "astronomical-observation-environment"
ROUTE = "earth"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


TARGETS = {
    "m31": {"title": "Andromeda Galaxy (M31)", "object_type": "galaxy", "ra_deg": 10.684708, "dec_deg": 41.26875},
    "m42": {"title": "Orion Nebula (M42)", "object_type": "emission nebula", "ra_deg": 83.822083, "dec_deg": -5.391111},
    "m51": {"title": "Whirlpool Galaxy (M51)", "object_type": "galaxy", "ra_deg": 202.469575, "dec_deg": 47.195258},
    "m87": {"title": "Messier 87 (M87)", "object_type": "elliptical galaxy", "ra_deg": 187.70593, "dec_deg": 12.391123},
    "crab": {"title": "Crab Nebula (M1)", "object_type": "supernova remnant", "ra_deg": 83.633083, "dec_deg": 22.0145},
    "galactic-center": {"title": "Galactic Center", "object_type": "galactic nucleus field", "ra_deg": 266.41683, "dec_deg": -29.00781},
}

SURVEYS = {
    "dss-optical": {
        "title": "Digitized Sky Survey",
        "wavelength": "optical",
        "survey_family": "DSS",
        "archive": "NASA/IPAC Infrared Science Archive (IRSA) Finder Chart",
        "archive_url": "https://irsa.ipac.caltech.edu/applications/finderchart/",
        "retrieval": "irsa-finderchart",
        "source_basis": "archival survey imagery",
        "color_semantics": "single-band or plate-derived display; not guaranteed natural color",
    },
    "2mass-near-ir": {
        "title": "2MASS",
        "wavelength": "near infrared",
        "survey_family": "2MASS",
        "archive": "NASA/IPAC Infrared Science Archive (IRSA) Finder Chart",
        "archive_url": "https://irsa.ipac.caltech.edu/applications/finderchart/",
        "retrieval": "irsa-finderchart",
        "source_basis": "archival survey imagery",
        "color_semantics": "infrared intensity/band products; visible appearance is not implied",
    },
    "wise-mid-ir": {
        "title": "WISE / AllWISE field imagery",
        "wavelength": "mid infrared",
        "survey_family": "WISE",
        "archive": "NASA/IPAC Infrared Science Archive (IRSA) Finder Chart",
        "archive_url": "https://irsa.ipac.caltech.edu/applications/finderchart/",
        "retrieval": "irsa-finderchart",
        "source_basis": "archival survey imagery",
        "color_semantics": "infrared intensity/band products; false-color displays may be used by source tools",
    },
    "galex-uv": {
        "title": "GALEX ultraviolet survey family",
        "wavelength": "ultraviolet",
        "survey_family": "GALEX",
        "archive": "NASA/GSFC HEASARC SkyView",
        "archive_url": "https://skyview.gsfc.nasa.gov/current/cgi/basicform.pl",
        "retrieval": "skyview",
        "source_basis": "archival survey imagery",
        "color_semantics": "ultraviolet intensity; visible color is representational",
    },
    "nvss-radio": {
        "title": "NVSS radio survey family",
        "wavelength": "radio",
        "survey_family": "NVSS",
        "archive": "NASA/GSFC HEASARC SkyView",
        "archive_url": "https://skyview.gsfc.nasa.gov/current/cgi/basicform.pl",
        "retrieval": "skyview",
        "source_basis": "archival survey imagery",
        "color_semantics": "radio intensity; display color is representational",
    },
    "rosat-soft-xray": {
        "title": "ROSAT soft X-ray survey family",
        "wavelength": "soft X-ray",
        "survey_family": "ROSAT",
        "archive": "NASA/GSFC HEASARC SkyView",
        "archive_url": "https://skyview.gsfc.nasa.gov/current/cgi/basicform.pl",
        "retrieval": "skyview",
        "source_basis": "archival survey imagery",
        "color_semantics": "X-ray intensity; display color is representational",
    },
    "planck-microwave": {
        "title": "Planck survey family",
        "wavelength": "microwave / submillimeter",
        "survey_family": "Planck",
        "archive": "NASA/GSFC HEASARC SkyView",
        "archive_url": "https://skyview.gsfc.nasa.gov/current/cgi/basicform.pl",
        "retrieval": "skyview",
        "source_basis": "archival all-sky survey products",
        "color_semantics": "frequency-map intensity; display color is representational",
    },
}


def _target(target_id: str, ra_deg: float | None, dec_deg: float | None) -> dict[str, Any]:
    tid = (target_id or "m31").lower()
    known = tid in TARGETS
    preset = TARGETS.get(tid, TARGETS["m31"])
    ra = preset["ra_deg"] if ra_deg is None else float(ra_deg)
    dec = preset["dec_deg"] if dec_deg is None else float(dec_deg)
    return {
        "target_id": tid if known else "custom",
        "title": preset["title"] if known else "Custom sky coordinate",
        "object_type": preset["object_type"] if known else "coordinate field",
        "ra_deg": round(ra % 360.0, 6),
        "dec_deg": round(max(-90.0, min(90.0, dec)), 6),
        "frame": "equatorial J2000",
    }


def _official_handoff(survey: dict[str, Any], target_state: dict[str, Any], field_deg: float) -> dict[str, Any]:
    if survey["retrieval"] == "irsa-finderchart":
        subset_arcmin = max(0.1, min(60.0, field_deg * 60.0))
        loc = f'{target_state["ra_deg"]} {target_state["dec_deg"]:+}'
        url = (
            "https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?"
            f"mode=getResult&locstr={quote(loc)}&survey={quote(survey['survey_family'])}"
            f"&subsetsize={subset_arcmin:.3f}&reproject=true"
        )
        return {
            "url": url,
            "service": "IRSA Finder Chart",
            "query_field_deg": round(subset_arcmin / 60.0, 6),
            "requested_field_was_clamped": field_deg > 1.0,
        }
    return {
        "url": survey["archive_url"],
        "service": "NASA HEASARC SkyView",
        "query_field_deg": round(field_deg, 6),
        "requested_field_was_clamped": False,
        "query_plan": {
            "position": f'{target_state["ra_deg"]}, {target_state["dec_deg"]}',
            "survey_family": survey["survey_family"],
            "coordinates": "J2000",
            "field_deg": round(field_deg, 6),
        },
    }


def overview() -> dict[str, Any]:
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "title": "Astronomical Observation Environment",
        "route": ROUTE,
        "parent_contract": "lunar-planetary-intelligence",
        "target_count": len(TARGETS),
        "survey_count": len(SURVEYS),
        "summary": "Continue beyond planetary observation into source-aware archival sky surveys without presenting an orientation field as telescope pixels or a virtual observatory as a live telescope.",
        "capabilities": [
            "deep-sky target presets and explicit J2000 coordinates",
            "multi-wavelength archival survey catalog",
            "NASA HEASARC SkyView and NASA/IPAC IRSA handoffs",
            "field-of-view state",
            "wavelength and color-semantics disclosure",
            "survey/source provenance",
            "astronomical evidence manifest",
            "Earth/orbit/planetary/deep-sky continuity",
        ],
        "truth_boundaries": [
            "The local sky field is orientation graphics unless verified survey pixels are explicitly loaded.",
            "SkyView is a virtual observatory over archived surveys, not a live telescope camera.",
            "Survey observations can come from different epochs, instruments, projections, pixel scales, and calibration pipelines.",
            "False-color or intensity mappings must not be interpreted as naked-eye color.",
            "Reprojection, resampling, mosaicking, smoothing, and contrast scaling can change presentation without changing the underlying source record.",
            "A named target does not guarantee coverage in every registered survey.",
        ],
        "generated_at": _now(),
    }
    p["contract_sha256"] = _digest(p)
    return p


def catalog() -> dict[str, Any]:
    rows = [{"id": sid, **survey, "live_telescope": False, "embedded_verified_pixels": False} for sid, survey in SURVEYS.items()]
    targets = [{"id": tid, **target, "coordinate_precision_note": "preset J2000 field center for navigation"} for tid, target in TARGETS.items()]
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "survey_count": len(rows), "target_count": len(targets), "surveys": rows, "targets": targets, "generated_at": _now()}


def target(target_id: str) -> dict[str, Any]:
    tid = (target_id or "").lower()
    if tid not in TARGETS:
        return {"ok": False, "version": VERSION, "contract": CONTRACT, "error": "unsupported target preset", "supported_targets": list(TARGETS)}
    p = {"ok": True, "version": VERSION, "contract": CONTRACT, "target_id": tid, "target": TARGETS[tid], "generated_at": _now()}
    p["target_sha256"] = _digest(p)
    return p


def state(target_id: str = "m31", survey_id: str = "dss-optical", ra_deg: float | None = None, dec_deg: float | None = None, field_deg: float = 0.25) -> dict[str, Any]:
    sid = survey_id if survey_id in SURVEYS else "dss-optical"
    survey = {"id": sid, **SURVEYS[sid]}
    target_state = _target(target_id, ra_deg, dec_deg)
    fov = max(0.01, min(10.0, float(field_deg)))
    handoff = _official_handoff(survey, target_state, fov)
    p = {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "mode": "astronomical-observation",
        "route": ROUTE,
        "target": target_state,
        "view": {"field_deg": round(fov, 6), "coordinate_frame": "equatorial J2000", "local_stage": "orientation-only star field"},
        "observation": {
            **survey,
            "official_observation_handoff": handoff,
            "observation_epoch": None,
            "coverage_verified_for_current_field": False,
        },
        "truth": {
            "local_orientation_is_survey_imagery": False,
            "live_telescope_feed_claimed": False,
            "real_time_observation_claimed": False,
            "natural_color_claimed": False,
            "official_archive_handoff_available": True,
            "boundary": "The local sky stage preserves target, survey, wavelength, and field state. Open the registered archive service for actual survey pixels until a verified image response is fetched and fingerprinted.",
        },
        "generated_at": _now(),
    }
    p["state_sha256"] = _digest(p)
    return p


def export_manifest(target_id: str = "m31", survey_id: str = "dss-optical", ra_deg: float | None = None, dec_deg: float | None = None, field_deg: float = 0.25) -> dict[str, Any]:
    s = state(target_id, survey_id, ra_deg, dec_deg, field_deg)
    return {
        "ok": True,
        "version": VERSION,
        "schema": "sc-site-intelligence-astronomical-view/1.0",
        "contract": CONTRACT,
        "astronomical_state": s,
        "review": {
            "survey_pixels_fabricated": False,
            "live_telescope_claimed": False,
            "official_source_link_preserved": True,
            "human_interpretation_required": True,
        },
        "manifest_sha256": _digest(s),
        "generated_at": _now(),
    }


def readiness() -> dict[str, Any]:
    checks = {
        "route_preserved": ROUTE == "earth",
        "target_presets_registered": len(TARGETS) >= 6,
        "multiwavelength_surveys_registered": len({survey["wavelength"] for survey in SURVEYS.values()}) >= 6,
        "irsa_registered": any("IRSA" in survey["archive"] for survey in SURVEYS.values()),
        "skyview_registered": any("SkyView" in survey["archive"] for survey in SURVEYS.values()),
        "no_fake_survey_pixels": True,
        "no_live_telescope_claim": True,
        "wavelength_semantics_disclosed": all(bool(survey["color_semantics"]) for survey in SURVEYS.values()),
    }
    p = {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"route": ROUTE, "targets": len(TARGETS), "surveys": len(SURVEYS)},
        "generated_at": _now(),
    }
    p["readiness_sha256"] = _digest(p)
    return p
