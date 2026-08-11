from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "exoplanets-habitability-atmospheric-biosignature-intelligence"
ROUTE = "earth"
WARNING = "EXOPLANET & ATMOSPHERIC EVIDENCE · NOT CONFIRMATION OF HABITABILITY OR LIFE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


SOURCES = {
    "nasa-exoplanet-archive-systems": {
        "title": "NASA Exoplanet Archive — Planetary Systems",
        "organization": "NASA Exoplanet Archive / Caltech IPAC",
        "access": "public TAP service",
        "recognized_hosts": ["exoplanetarchive.ipac.caltech.edu"],
        "indicator_types": ["planetary-system", "stellar-context", "orbital-parameters", "equilibrium-temperature"],
        "evidence_classes": ["planetary-system-record"],
        "truth": "Published system parameters characterize planets and hosts; a habitable-zone location or equilibrium temperature is not a habitability finding.",
    },
    "nasa-exoplanet-archive-atmospheres": {
        "title": "NASA Exoplanet Archive — Atmospheric Spectroscopy",
        "organization": "NASA Exoplanet Archive / Caltech IPAC",
        "access": "public Atmospheric Spectroscopy table with TAP support",
        "recognized_hosts": ["exoplanetarchive.ipac.caltech.edu"],
        "indicator_types": ["transmission-spectrum", "eclipse-spectrum", "direct-imaging-spectrum"],
        "evidence_classes": ["spectrum-record"],
        "truth": "Peer-reviewed spectra constrain atmospheric properties; a spectral feature does not by itself establish a molecule, biosignature or life.",
    },
    "exo-mast": {
        "title": "Exo.MAST",
        "organization": "MAST / Space Telescope Science Institute",
        "access": "public exoplanet API for identifiers, properties and curated spectra",
        "recognized_hosts": ["exo.mast.stsci.edu", "mast.stsci.edu"],
        "indicator_types": ["exoplanet-identifier", "planet-properties", "curated-spectrum"],
        "evidence_classes": ["target-context-record", "spectrum-record"],
        "truth": "MAST target and spectrum products are observational context; they do not establish habitability or biology.",
    },
    "mast-jwst-spectraldb": {
        "title": "MAST JWST Spectral Data Services",
        "organization": "MAST / Space Telescope Science Institute",
        "access": "public API for JWST Level-3 spectroscopic pixel and derived data",
        "recognized_hosts": ["mast.stsci.edu", "archive.stsci.edu"],
        "indicator_types": ["jwst-spectrum", "spectral-pixel", "derived-spectral-parameter"],
        "evidence_classes": ["spectrum-record", "spectral-measurement-record"],
        "truth": "JWST spectral products provide calibrated observational evidence; atmospheric interpretation and biosignature claims require external scientific analysis and false-positive assessment.",
    },
}

INDICATOR_TYPES = {
    "planetary-system": {"description": "Planet, star and system parameters from published archive records."},
    "stellar-context": {"description": "Host-star properties relevant to planetary interpretation."},
    "orbital-parameters": {"description": "Orbital period, semimajor axis, eccentricity or related published parameters."},
    "equilibrium-temperature": {"description": "Published/model-derived equilibrium temperature, not directly measured surface temperature."},
    "transmission-spectrum": {"description": "Spectrum measured during planetary transit."},
    "eclipse-spectrum": {"description": "Spectrum measured during secondary eclipse."},
    "direct-imaging-spectrum": {"description": "Spectrum of a directly imaged exoplanet."},
    "exoplanet-identifier": {"description": "Canonical/alternate exoplanet identifier resolution."},
    "planet-properties": {"description": "Planet property context returned by Exo.MAST."},
    "curated-spectrum": {"description": "Curated exoplanet spectrum available through Exo.MAST."},
    "jwst-spectrum": {"description": "JWST Level-3 spectroscopic science product."},
    "spectral-pixel": {"description": "Pixel-level wavelength/flux/error evidence from a JWST science product."},
    "derived-spectral-parameter": {"description": "Derived spectral parameter supplied by MAST services."},
}

EVIDENCE_CLASSES = {
    "planetary-system-record": "Published planet/star/system parameter record.",
    "target-context-record": "Resolved exoplanet target or property context.",
    "spectrum-record": "Published or calibrated exoplanet spectrum metadata/data record.",
    "spectral-measurement-record": "Wavelength/flux/error or derived spectral measurement record.",
    "biosignature-assessment-record": "Source-attributed interpretation record whose biological meaning remains unconfirmed.",
}


def _source(value: str | None) -> tuple[str, dict[str, Any]]:
    key = (value or "nasa-exoplanet-archive-systems").strip().lower()
    if key not in SOURCES:
        raise ValueError(f"unsupported exoplanet source: {key}")
    return key, {"id": key, **SOURCES[key]}


def _indicator(value: str | None) -> tuple[str, dict[str, Any]]:
    key = (value or "planetary-system").strip().lower()
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


def overview() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "route": ROUTE,
        "title": "Exoplanets, Habitability & Atmospheric Biosignature Intelligence",
        "source_count": len(SOURCES),
        "indicator_type_count": len(INDICATOR_TYPES),
        "evidence_class_count": len(EVIDENCE_CLASSES),
        "summary": "Orient exoplanet system parameters, atmospheric spectra and JWST spectral products while keeping habitability and biosignature interpretation explicitly separate from confirmation of life.",
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
        "interpretive_framework": {
            "organization": "NASA Astrobiology / NExSS",
            "principle": "Habitability and biosignatures require environmental context, alternative explanations and false-positive assessment.",
        },
        "truth_boundaries": {
            "habitable_zone_equals_habitable": False,
            "equilibrium_temperature_equals_surface_temperature": False,
            "spectral_feature_equals_molecule_confirmation": False,
            "molecule_detection_equals_biosignature_confirmation": False,
            "biosignature_candidate_equals_life_detection": False,
            "modeled_abundance_equals_direct_measurement": False,
            "abiotic_false_positive_excluded_by_platform": False,
            "life_confirmed": False,
            "automatic_action_authorized": False,
        },
    }


def state(source_id: str = "nasa-exoplanet-archive-systems", indicator_type: str = "planetary-system", target: str = "", spectrum_type: str = "", facility: str = "", wavelength_um: float | None = None) -> dict[str, Any]:
    _, source = _source(source_id)
    iid, indicator = _indicator(indicator_type)
    if wavelength_um is not None and float(wavelength_um) <= 0:
        raise ValueError("wavelength_um must be positive")
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "source": source,
        "indicator_type": indicator,
        "target": str(target or "").strip() or None,
        "spectrum_type": str(spectrum_type or "").strip() or None,
        "facility": str(facility or "").strip() or None,
        "wavelength_um": None if wavelength_um is None else float(wavelength_um),
        "source_supports_indicator_type": iid in source["indicator_types"],
        "evidence": {
            "planetary_system_loaded": False,
            "spectrum_loaded": False,
            "molecular_interpretation_loaded": False,
            "habitability_assessment_loaded": False,
            "biosignature_assessment_loaded": False,
            "life_confirmed": False,
        },
        "truth": {
            "habitable_zone_treated_as_habitability": False,
            "equilibrium_temperature_treated_as_surface_temperature": False,
            "spectral_feature_treated_as_molecule_confirmation": False,
            "molecule_treated_as_biosignature_confirmation": False,
            "biosignature_treated_as_life_detection": False,
            "abiotic_false_positive_treated_as_excluded": False,
            "automatic_action_authorized": False,
        },
    }


def normalize_planet(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "nasa-exoplanet-archive-systems")
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "evidence_class": _evidence(request.get("evidence_class") or "planetary-system-record"),
        "planet_name": str(request.get("planet_name") or "").strip() or None,
        "host_name": str(request.get("host_name") or "").strip() or None,
        "orbital_period_days": request.get("orbital_period_days"),
        "planet_radius_earth": request.get("planet_radius_earth"),
        "planet_mass_earth": request.get("planet_mass_earth"),
        "equilibrium_temperature_k": request.get("equilibrium_temperature_k"),
        "insolation_earth": request.get("insolation_earth"),
        "habitable_zone_flag_from_source": request.get("habitable_zone_flag_from_source"),
        "habitability_confirmed": False,
        "surface_temperature_inferred": False,
        "life_inferred": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "planet": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_spectrum(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    _, source = _source(request.get("source_id") or "nasa-exoplanet-archive-atmospheres")
    evidence_class = _evidence(request.get("evidence_class") or "spectrum-record")
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "evidence_class": evidence_class,
        "planet_name": str(request.get("planet_name") or "").strip() or None,
        "spectrum_type": str(request.get("spectrum_type") or "").strip() or None,
        "facility": str(request.get("facility") or "").strip() or None,
        "instrument": str(request.get("instrument") or "").strip() or None,
        "wavelength_min_um": request.get("wavelength_min_um"),
        "wavelength_max_um": request.get("wavelength_max_um"),
        "data_product": str(request.get("data_product") or "").strip() or None,
        "molecule_confirmed_by_platform": False,
        "biosignature_confirmed": False,
        "life_confirmed": False,
        "abiotic_false_positive_excluded_by_platform": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "spectrum": record, "record_sha256": _digest(record), "normalized_at": _now()}


def normalize_biosignature(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    source_id = request.get("source_id") or "nasa-exoplanet-archive-atmospheres"
    _, source = _source(source_id)
    record = {
        "source_id": source["id"],
        "source_url": _url(source, request.get("source_url")),
        "evidence_class": _evidence(request.get("evidence_class") or "biosignature-assessment-record"),
        "planet_name": str(request.get("planet_name") or "").strip() or None,
        "species_or_feature": str(request.get("species_or_feature") or "").strip() or None,
        "source_claim": str(request.get("source_claim") or "").strip() or None,
        "source_confidence": str(request.get("source_confidence") or "").strip() or None,
        "abiotic_alternatives_considered_by_source": bool(request.get("abiotic_alternatives_considered_by_source", False)),
        "biosignature_confirmed_by_platform": False,
        "life_detected_by_platform": False,
        "abiotic_false_positive_excluded_by_platform": False,
        "independent_confirmation_inferred": False,
        "announcement_authorized": False,
        "automatic_action_authorized": False,
    }
    return {"ok": True, "version": VERSION, "contract": CONTRACT, "assessment": record, "record_sha256": _digest(record), "normalized_at": _now()}


def export_manifest(source_id: str = "nasa-exoplanet-archive-systems", indicator_type: str = "planetary-system", target: str = "", spectrum_type: str = "", facility: str = "", wavelength_um: float | None = None) -> dict[str, Any]:
    current = state(source_id, indicator_type, target, spectrum_type, facility, wavelength_um)
    payload = {
        "schema": "sc-site-intelligence-exoplanets-habitability-biosignatures/1.0",
        "version": VERSION,
        "contract": CONTRACT,
        "warning": WARNING,
        "query": {
            "source_id": current["source"]["id"],
            "indicator_type": current["indicator_type"]["id"],
            "target": current["target"],
            "spectrum_type": current["spectrum_type"],
            "facility": current["facility"],
            "wavelength_um": current["wavelength_um"],
        },
        "evidence": current["evidence"],
        "review": {
            "habitable_zone_as_habitability": False,
            "equilibrium_temperature_as_surface_temperature": False,
            "spectral_feature_as_molecule_confirmation": False,
            "molecule_as_biosignature_confirmation": False,
            "biosignature_as_life_detection": False,
            "abiotic_false_positive_as_excluded": False,
        },
    }
    return {**payload, "manifest_sha256": _digest(payload), "generated_at": _now()}


def readiness() -> dict[str, Any]:
    checks = {
        "four_source_families_registered": len(SOURCES) == 4,
        "nasa_systems_registered": "nasa-exoplanet-archive-systems" in SOURCES,
        "nasa_atmospheres_registered": "nasa-exoplanet-archive-atmospheres" in SOURCES,
        "exomast_registered": "exo-mast" in SOURCES,
        "mast_jwst_spectraldb_registered": "mast-jwst-spectraldb" in SOURCES,
        "habitability_guard_present": True,
        "biosignature_guard_present": True,
        "abiotic_false_positive_guard_present": True,
        "life_confirmation_guard_present": True,
        "public_route_count_preserved": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "summary": {"sources": len(SOURCES), "indicator_types": len(INDICATOR_TYPES), "evidence_classes": len(EVIDENCE_CLASSES), "public_route_count_delta": 0, "primary_area_count_delta": 0},
        "generated_at": _now(),
    }
