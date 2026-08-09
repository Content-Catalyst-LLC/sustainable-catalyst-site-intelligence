"""Record-level provenance and indicator truth for Site Intelligence v4.5.0.

This module deliberately separates a reproducible provenance fingerprint from any
claim that a source record is authoritative, complete, or current. A fingerprint
only proves that the disclosed canonical record did not change within this
response; it does not validate the upstream publisher's content.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
import json

from .config import Settings
from .data_truth_v32371 import GlobalCountryDataTruth
from .live_country_intelligence import INDICATORS
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-record-provenance/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
RECORD_TYPES = ("indicator", "event", "map_layer", "chart", "table_record")
TRUTH_STATES = ("observed", "historical_snapshot", "context_only", "missing", "unverified", "unavailable")

MAP_LAYERS: dict[str, dict[str, str]] = {
    "true-color": {
        "title": "NASA Corrected Reflectance True Color",
        "source": "NASA EOSDIS Global Imagery Browse Services",
        "source_url": "https://worldview.earthdata.nasa.gov/",
        "category": "earth_observation",
        "interpretation": "Daily global visual context for clouds, smoke, land, water, and large-scale events.",
    },
    "land-surface-temperature": {
        "title": "MODIS Terra Land Surface Temperature Day",
        "source": "NASA EOSDIS Global Imagery Browse Services",
        "source_url": "https://worldview.earthdata.nasa.gov/",
        "category": "climate_heat",
        "interpretation": "Surface-temperature context; not an air-temperature measurement or local instrument reading.",
    },
    "fires-thermal-anomalies": {
        "title": "MODIS Terra Fires and Thermal Anomalies",
        "source": "NASA EOSDIS Global Imagery Browse Services",
        "source_url": "https://worldview.earthdata.nasa.gov/",
        "category": "fire",
        "interpretation": "Thermal-anomaly context for wildfire and high-temperature event orientation.",
    },
    "vegetation-index": {
        "title": "MODIS Terra Vegetation Index",
        "source": "NASA EOSDIS Global Imagery Browse Services",
        "source_url": "https://worldview.earthdata.nasa.gov/",
        "category": "vegetation",
        "interpretation": "Vegetation-condition context for drought, land cover, and ecological analysis.",
    },
    "precipitation-rate": {
        "title": "IMERG Precipitation Rate",
        "source": "NASA EOSDIS Global Imagery Browse Services",
        "source_url": "https://worldview.earthdata.nasa.gov/",
        "category": "hydrology",
        "interpretation": "Satellite-derived precipitation-rate context for storm and water-cycle monitoring.",
    },
}



def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _safe_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_url(value: Any) -> str | None:
    raw = _safe_text(value, 1600)
    if not raw:
        return None
    parsed = urlparse(raw)
    return raw if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _iso3(value: Any) -> str:
    code = _safe_text(value, 3).upper()
    if len(code) != 3 or not code.isalpha():
        raise KeyError(code)
    return code


def _indicator_definition(indicator_id: str) -> Mapping[str, str]:
    key = _safe_text(indicator_id, 80)
    for item in INDICATORS:
        if item["id"] == key or item["key"] == key:
            return item
    raise KeyError(key)


def _record_envelope(payload: Mapping[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    generated = generated_at or _now()
    canonical_payload = json.loads(_canonical({k: v for k, v in payload.items() if k not in {"fingerprint", "generated_at"}}))
    dates = canonical_payload.get("dates")
    if isinstance(dates, dict):
        dates.pop("generated_at", None)
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_id": RELEASE_ID,
        "schema": SCHEMA_VERSION,
        "generated_at": generated,
        **payload,
        "fingerprint": {
            "algorithm": "sha256",
            "canonicalization": "sorted-json-utf8",
            "value": _fingerprint(canonical_payload),
            "meaning": "Detects changes to this disclosed canonical record; it does not validate upstream accuracy or authority.",
        },
    }


class RecordProvenanceCenter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.country_truth = GlobalCountryDataTruth(settings)

    def indicator(self, country_code: str, indicator_id: str) -> dict[str, Any]:
        code = _iso3(country_code)
        definition = _indicator_definition(indicator_id)
        country_payload = self.country_truth.country_indicators(code)
        row = next(item for item in country_payload["indicators"] if item["indicator_id"] == definition["id"])
        country = country_payload["country"]
        value = row.get("value")
        year = row.get("observation_year")
        coverage_state = str(row.get("coverage_state") or "unknown")
        if value is None:
            truth_state = "missing"
            assertion = "No verified observation is included in this release."
        elif coverage_state == "historical_only":
            truth_state = "historical_snapshot"
            assertion = "A dated reference snapshot is disclosed and is not presented as live retrieval."
        else:
            truth_state = "observed"
            assertion = "A source-linked observation is disclosed with its retrieval and transformation state."
        iso2 = country.get("iso2")
        source_url = f"https://data.worldbank.org/indicator/{definition['id']}"
        if iso2:
            source_url += f"?locations={iso2}"
        observation_at = f"{int(year):04d}-12-31T00:00:00+00:00" if year else None
        record_id = f"indicator:{code}:{definition['id']}"
        return _record_envelope({
            "contract": "record-provenance-indicator",
            "record_id": record_id,
            "record_type": "indicator",
            "truth_state": truth_state,
            "presentation_state": coverage_state,
            "country": {"code": code, "name": country.get("name")},
            "title": definition["label"],
            "value": {"number": value, "text": None if value is None else str(value), "available": value is not None},
            "units": {"original": definition["unit"], "display": definition["unit"], "conversion_applied": False},
            "dates": {"observation_at": observation_at, "observation_year": year, "retrieved_at": None, "generated_at": _now()},
            "source": {
                "feed_id": "world_bank",
                "publisher": "World Bank Open Data",
                "indicator_id": definition["id"],
                "url": source_url,
                "license": "Source terms apply; verify current reuse terms at the publisher.",
            },
            "transformations": [
                {"step": 1, "operation": "source-field-selection", "detail": "Select the latest disclosed non-null observation or the explicitly dated packaged snapshot."},
                {"step": 2, "operation": "type-normalization", "detail": "Preserve the numeric value without imputation."},
                {"step": 3, "operation": "unit-presentation", "detail": "Display the source unit without conversion."},
                {"step": 4, "operation": "truth-classification", "detail": f"Classify the record as {truth_state}; coverage state remains {coverage_state}."},
            ],
            "lineage": {
                "evidence_level": row.get("evidence_level"),
                "source_feed_id": row.get("source_feed_id"),
                "country_truth_endpoint": f"/public/data-truth/country/{code}/indicators",
                "record_truth_endpoint": f"/public/record-truth/indicator/{code}/{definition['id']}",
            },
            "assertion": assertion,
            "limitations": [
                row.get("reason"),
                "Missing observations remain missing and are not imputed or replaced with another country’s value.",
                "Indicators may use different reporting years, definitions, revisions, and national methodologies.",
                "This descriptive record does not establish causality, ranking, eligibility, liability, or policy effectiveness.",
                "A provenance fingerprint is not a certification of upstream accuracy.",
            ],
        })

    def country_catalog(self, country_code: str) -> dict[str, Any]:
        code = _iso3(country_code)
        records = [self.indicator(code, item["id"]) for item in INDICATORS]
        country = records[0]["country"] if records else self.country_truth._country(code)
        summary = {state: sum(1 for record in records if record["truth_state"] == state) for state in TRUTH_STATES}
        return _record_envelope({
            "contract": "country-record-provenance-catalog",
            "record_type": "catalog",
            "country": country,
            "record_count": len(records),
            "summary": summary,
            "records": records,
            "export_endpoint": f"/public/record-truth/manifest?country={code}",
            "boundaries": [
                "Catalog inclusion means the record has a truth contract, not that a current observation exists.",
                "Missing records remain missing and are not imputed.",
            ],
        })

    def map_layer(self, layer_id: str, *, date: str | None = None) -> dict[str, Any]:
        layer = MAP_LAYERS.get(_safe_text(layer_id, 160))
        if layer is None:
            raise KeyError(layer_id)
        normalized_date = _safe_text(date, 32) or None
        return _record_envelope({
            "contract": "record-provenance-map-layer",
            "record_id": f"map-layer:{layer_id}:{normalized_date or 'unspecified'}",
            "record_type": "map_layer",
            "truth_state": "context_only",
            "presentation_state": "context_only",
            "title": layer["title"],
            "value": {"available": True, "text": "Raster imagery layer"},
            "units": {"original": None, "display": None, "conversion_applied": False},
            "dates": {"observation_at": normalized_date, "retrieved_at": None, "generated_at": _now()},
            "source": {"feed_id": "nasa_gibs", "publisher": layer["source"], "url": layer["source_url"], "license": "NASA Earthdata source terms apply."},
            "transformations": [
                {"step": 1, "operation": "tile-selection", "detail": "Request the selected public imagery layer for the displayed date."},
                {"step": 2, "operation": "visual-composition", "detail": "Render source tiles with user-controlled opacity above the basemap."},
                {"step": 3, "operation": "no-pixel-inference", "detail": "No automatic conclusion is derived from displayed pixels."},
            ],
            "assertion": layer["interpretation"],
            "limitations": [
                "Imagery may contain cloud cover, mosaicking, temporal gaps, projection effects, and resolution limits.",
                "Displayed imagery is contextual evidence and is not a field measurement, legal boundary, or automated finding.",
            ],
        })

    def normalize_record(self, record: Mapping[str, Any]) -> dict[str, Any]:
        record_type = _safe_text(record.get("record_type") or "table_record", 40).lower().replace("-", "_")
        if record_type not in RECORD_TYPES:
            record_type = "table_record"
        source_url = _safe_url(record.get("source_url"))
        observed_at = _safe_text(record.get("observed_at"), 80) or None
        retrieved_at = _safe_text(record.get("retrieved_at"), 80) or None
        state = _safe_text(record.get("data_state") or "unverified", 60).lower().replace("-", "_")
        truth_state = "observed" if state in {"live", "observed", "current"} and source_url else "unverified"
        if state in {"stale", "cached", "reference_snapshot", "historical"}:
            truth_state = "historical_snapshot"
        if state in {"unavailable", "failed"}:
            truth_state = "unavailable"
        identifier = _safe_text(record.get("id") or record.get("record_id") or record.get("event_id"), 220)
        canonical_identity = {
            "record_type": record_type,
            "identifier": identifier,
            "title": _safe_text(record.get("title") or record.get("label") or "Public record", 300),
            "source": _safe_text(record.get("source") or record.get("source_name") or "Source not declared", 240),
            "source_url": source_url,
            "observed_at": observed_at,
            "country_code": _safe_text(record.get("country_code"), 3).upper() or None,
            "value": record.get("value"),
            "unit": _safe_text(record.get("unit"), 100) or None,
        }
        stable_id = identifier or _fingerprint(canonical_identity)[:24]
        return _record_envelope({
            "contract": "record-provenance-normalized-public-record",
            "record_id": f"{record_type}:{stable_id}",
            "record_type": record_type,
            "truth_state": truth_state,
            "presentation_state": state,
            "country": {"code": canonical_identity["country_code"], "name": _safe_text(record.get("country"), 160) or None},
            "title": canonical_identity["title"],
            "value": {"number": record.get("value") if isinstance(record.get("value"), (int, float)) else None, "text": None if record.get("value") is None else _safe_text(record.get("value"), 240), "available": record.get("value") is not None},
            "units": {"original": canonical_identity["unit"], "display": canonical_identity["unit"], "conversion_applied": False},
            "dates": {"observation_at": observed_at, "retrieved_at": retrieved_at, "generated_at": _now()},
            "source": {"feed_id": _safe_text(record.get("source_id"), 120) or None, "publisher": canonical_identity["source"], "url": source_url, "license": _safe_text(record.get("license"), 300) or "Not declared in the supplied record."},
            "transformations": [
                {"step": 1, "operation": "public-field-selection", "detail": "Retain only public-safe fields supplied by the active workspace."},
                {"step": 2, "operation": "text-and-url-normalization", "detail": "Normalize whitespace and reject non-HTTP(S) source URLs."},
                {"step": 3, "operation": "truth-classification", "detail": "Classify from disclosed source URL, timestamps, and data-state labels without external verification."},
            ],
            "assertion": _safe_text(record.get("summary") or record.get("description") or record.get("interpretation") or "The record is disclosed for inspection; no additional conclusion is inferred.", 600),
            "limitations": [
                "This endpoint normalizes the supplied public record but does not independently contact or validate the upstream source.",
                "The fingerprint detects changes to the normalized disclosure, not changes at the upstream publisher.",
                "Missing source, date, unit, geography, or licensing fields remain missing.",
            ],
        })

    def manifest(self, country_code: str) -> dict[str, Any]:
        catalog = self.country_catalog(country_code)
        entries = [
            {
                "record_id": record["record_id"],
                "record_type": record["record_type"],
                "truth_state": record["truth_state"],
                "fingerprint": record["fingerprint"]["value"],
                "source_url": record["source"]["url"],
                "observation_at": record["dates"]["observation_at"],
            }
            for record in catalog["records"]
        ]
        layer_entries = [
            {
                "record_id": record["record_id"],
                "record_type": record["record_type"],
                "truth_state": record["truth_state"],
                "fingerprint": record["fingerprint"]["value"],
                "source_url": record["source"]["url"],
                "observation_at": record["dates"]["observation_at"],
            }
            for record in (self.map_layer(layer_id) for layer_id in MAP_LAYERS)
        ]
        entries.extend(layer_entries)
        manifest_payload = {
            "country": catalog["country"],
            "entry_count": len(entries),
            "entries": entries,
            "method": "sha256 over each canonical record truth response",
        }
        return _record_envelope({
            "contract": "record-provenance-export-manifest",
            "record_type": "manifest",
            **manifest_payload,
            "manifest_fingerprint": _fingerprint(manifest_payload),
            "boundaries": [
                "The manifest contains disclosed record fingerprints, not source files or independent source verification.",
                "Recreate or export a new manifest when record truth responses change.",
            ],
        })


def public_indicator_record_truth(settings: Settings, country_code: str, indicator_id: str) -> dict[str, Any]:
    return RecordProvenanceCenter(settings).indicator(country_code, indicator_id)


def public_country_record_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    return RecordProvenanceCenter(settings).country_catalog(country_code)


def public_map_layer_truth(settings: Settings, layer_id: str, date: str | None = None) -> dict[str, Any]:
    return RecordProvenanceCenter(settings).map_layer(layer_id, date=date)


def public_normalized_record_truth(settings: Settings, record: Mapping[str, Any]) -> dict[str, Any]:
    return RecordProvenanceCenter(settings).normalize_record(record)


def public_record_truth_manifest(settings: Settings, country_code: str) -> dict[str, Any]:
    return RecordProvenanceCenter(settings).manifest(country_code)
