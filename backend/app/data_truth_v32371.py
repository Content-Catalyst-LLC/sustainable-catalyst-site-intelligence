"""Global country data truth and coverage matrix for Site Intelligence v4.35.23."""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping
import json

from .config import Settings
from .data_truth_v3233 import DataTruthCenter as SourceTruthCenter
from .live_country_intelligence import FALLBACKS, INDICATORS
from .country_identity_v43523 import country_identity_registry
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-global-country-data-truth/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
COVERAGE_STATES = ("available", "partial", "no_recent_records", "historical_only", "not_applicable", "unavailable", "unknown")
DEFAULT_MATRIX_COUNTRIES = ("KEN","GHA","USA","IND","BRA","DEU","AUS","CHN","ZAF","NGA","JPN","MEX","EGY","GBR","FRA","CAN","IDN","ARG","PAK","ETH")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _code(value: Any) -> str:
    code = str(value or "").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise KeyError(code)
    return code


@lru_cache(maxsize=1)
def _bundled_country_catalog() -> dict[str, dict[str, Any]]:
    # v4.35.23: Data Truth and the interactive selector share one canonical
    # first-party identity registry. This eliminates split catalog behavior where
    # the selector could expose a country that downstream routing could not resolve.
    rows = {}
    for code, record in country_identity_registry().items():
        rows[code] = {
            "code": code,
            "iso2": record.get("iso2"),
            "name": record.get("name") or code,
            "region": record.get("region") or record.get("continent") or "Unclassified",
            "continent": record.get("continent") or record.get("region") or "Unclassified",
            "capital": record.get("capital"),
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude"),
            "alternate_names": record.get("alternate_names") or [],
            "catalog_source": "bundled-canonical-country-identity-v43523",
        }
    return dict(sorted(rows.items(), key=lambda item: (item[1]["name"], item[0])))



class GlobalCountryDataTruth:
    """Country-aware truth without silently converting eligibility into observed coverage."""

    def __init__(self, settings: Settings, source_center: SourceTruthCenter | None = None) -> None:
        self.settings = settings
        self.source_center = source_center or SourceTruthCenter(settings)

    def _country(self, country_code: str) -> dict[str, Any]:
        code = _code(country_code)
        country = _bundled_country_catalog().get(code)
        if country is None:
            raise KeyError(code)
        return country

    @staticmethod
    def _eligible(policy: Mapping[str, Any], code: str) -> bool:
        if policy.get("eligible") == "global":
            return True
        eligible = {str(item).upper() for item in policy.get("eligible_iso3") or []}
        return code in eligible

    def _country_source(self, source: Mapping[str, Any], country: Mapping[str, Any]) -> dict[str, Any]:
        policy = source.get("geographic_policy") or {}
        code = str(country["code"])
        eligible = self._eligible(policy, code)
        scope = str(policy.get("scope") or "undeclared")
        runtime = source.get("retrieval") or {}
        data_state = source.get("data_state") or {}
        counts = (source.get("runtime") or {}).get("country_record_counts") or {}
        count = counts.get(code) if isinstance(counts, Mapping) else None
        evidence_level = "contract_only"
        state = "not_applicable" if not eligible else str(policy.get("default_country_state") or "unknown")
        reason = str(policy.get("boundary") or "Country coverage has not been verified.")

        if not eligible:
            state = "not_applicable"
            reason = "The source contract does not apply to this country. " + reason
        elif data_state.get("presentation") == "unavailable" and runtime.get("last_status") not in {"never_run", None}:
            state = "unavailable"
            evidence_level = "runtime"
            reason = "The source applies geographically, but its current retrieval operation is unavailable."
        elif count is not None:
            evidence_level = "observed_runtime"
            count = max(0, int(count))
            if count > 0:
                state = "historical_only" if policy.get("observation_mode") == "periodic" else "available"
                reason = f"The latest recorded source run returned {count} country-linked record(s)."
            elif policy.get("observation_mode") == "event_driven":
                state = "no_recent_records"
                reason = "The latest recorded source run returned no country-linked records; this is not evidence that the condition is absent."
        elif source.get("feed_id") == "world_bank" and code in FALLBACKS:
            state = "historical_only"
            evidence_level = "packaged_snapshot"
            reason = "The release includes explicitly dated packaged indicator snapshots for this country; live retrieval remains independently disclosed."

        if state not in COVERAGE_STATES:
            state = "unknown"
        return {
            "feed_id": source.get("feed_id"),
            "label": source.get("label"),
            "publisher": source.get("publisher"),
            "category": source.get("category"),
            "domain": policy.get("domain") or source.get("category"),
            "country": {"code": code, "name": country.get("name")},
            "eligibility": "eligible" if eligible else "not_applicable",
            "coverage_state": state,
            "evidence_level": evidence_level,
            "country_record_count": count,
            "country_resolution": policy.get("country_resolution", "undeclared"),
            "observation_mode": policy.get("observation_mode", "undeclared"),
            "reason": reason,
            "operational_state": data_state.get("presentation", "unknown"),
            "last_success_at": runtime.get("last_success_at"),
            "freshness": runtime.get("freshness", "unknown"),
            "source_truth_url": f"/public/data-truth/{source.get('feed_id')}",
        }

    @staticmethod
    def _summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        summary = {state: 0 for state in COVERAGE_STATES}
        summary.update({"eligible": 0, "not_eligible": 0, "observed": 0, "contract_only": 0})
        for row in rows:
            state = str(row.get("coverage_state") or "unknown")
            summary[state] = summary.get(state, 0) + 1
            summary["eligible" if row.get("eligibility") == "eligible" else "not_eligible"] += 1
            if row.get("evidence_level") in {"observed_runtime", "packaged_snapshot"}:
                summary["observed"] += 1
            else:
                summary["contract_only"] += 1
        return summary

    def countries(self) -> dict[str, Any]:
        catalog = list(_bundled_country_catalog().values())
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-country-data-truth-catalog", "generated_at": _now(),
            "country_count": len(catalog), "countries": catalog,
            "boundaries": [
                "The country catalog establishes selectable geography, not source or indicator availability.",
                "A source marked geographically eligible may still have no country-linked records.",
            ],
        }

    def country_sources(self, country_code: str) -> dict[str, Any]:
        country = self._country(country_code)
        source_payload = self.source_center.directory()
        rows = [self._country_source(source, country) for source in source_payload["sources"]]
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "country-source-data-truth", "generated_at": _now(), "country": country,
            "source_count": len(rows), "summary": self._summary(rows), "sources": rows,
            "coverage_policy": {
                "states": list(COVERAGE_STATES), "eligibility_is_observation": False,
                "zero_records_proves_absence": False, "unknown_is_available": False,
            },
        }

    def country_indicators(self, country_code: str) -> dict[str, Any]:
        country = self._country(country_code)
        fallback = FALLBACKS.get(country["code"], {})
        rows = []
        for definition in INDICATORS:
            snapshot = fallback.get(definition["key"])
            if snapshot:
                value, year = snapshot
                state, evidence, reason = "historical_only", "packaged_snapshot", "A dated packaged fallback is present and is never represented as live."
            else:
                value, year = None, None
                state, evidence, reason = "unknown", "contract_only", "The World Bank connector is eligible, but this release does not include a verified country-series observation."
            rows.append({
                "indicator_id": definition["id"], "key": definition["key"], "label": definition["label"],
                "domain": definition["domain"], "unit": definition["unit"], "coverage_state": state,
                "evidence_level": evidence, "value": value, "observation_year": year, "source_feed_id": "world_bank",
                "reason": reason,
            })
        summary = {state: sum(1 for row in rows if row["coverage_state"] == state) for state in COVERAGE_STATES}
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "country-indicator-data-truth", "generated_at": _now(), "country": country,
            "indicator_count": len(rows), "summary": summary, "indicators": rows,
            "boundaries": ["Missing indicator records remain missing and are not imputed.", "Packaged snapshots are historical fallbacks, not live retrievals."],
        }

    def country(self, country_code: str) -> dict[str, Any]:
        sources = self.country_sources(country_code)
        indicators = self.country_indicators(country_code)
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-country-data-truth", "generated_at": _now(), "country": sources["country"],
            "summary": sources["summary"], "source_count": sources["source_count"], "sources": sources["sources"],
            "indicators": indicators["indicators"], "indicator_summary": indicators["summary"],
            "endpoints": {
                "sources": f"/public/data-truth/country/{sources['country']['code']}/sources",
                "indicators": f"/public/data-truth/country/{sources['country']['code']}/indicators",
                "matrix": f"/public/data-truth/coverage-matrix?countries={sources['country']['code']}",
            },
            "boundaries": [
                "Geographic eligibility is disclosed separately from observed records.",
                "No recent records does not establish that a hazard, crisis, alert, or condition is absent.",
                "Unknown coverage remains unknown and is not upgraded to available.",
            ],
        }

    def matrix(self, *, countries: Iterable[str] | None = None, region: str = "", source_id: str = "", state: str = "", limit: int = 24, offset: int = 0) -> dict[str, Any]:
        catalog = _bundled_country_catalog()
        requested = []
        for value in countries or DEFAULT_MATRIX_COUNTRIES:
            try:
                code = _code(value)
            except KeyError:
                continue
            if code in catalog and code not in requested:
                requested.append(code)
        if region:
            term = region.strip().lower()
            requested = [code for code in (requested or catalog.keys()) if term in str(catalog[code].get("region") or "").lower()]
        if not requested:
            requested = list(catalog.keys())
        requested = requested[max(0, offset):max(0, offset)+max(1, min(int(limit), 60))]
        source_rows = self.source_center.directory()["sources"]
        if source_id:
            key = source_id.strip().lower().replace("-", "_")
            source_rows = [row for row in source_rows if row.get("feed_id") == key]
        columns = [{"feed_id": row.get("feed_id"), "label": row.get("label"), "domain": (row.get("geographic_policy") or {}).get("domain") or row.get("category")} for row in source_rows]
        rows=[]
        matrix_summary={coverage_state:0 for coverage_state in COVERAGE_STATES}
        for code in requested:
            country=catalog[code]
            cells=[]
            for source in source_rows:
                cell=self._country_source(source,country)
                if state and cell["coverage_state"] != state:
                    continue
                matrix_summary[cell["coverage_state"]]+=1
                cells.append({k:cell[k] for k in ("feed_id","coverage_state","eligibility","evidence_level","country_record_count","reason")})
            if cells:
                rows.append({"country":country,"summary":self._summary(cells),"cells":cells})
        return {
            "ok": True, "version": APP_VERSION, "release_id": RELEASE_ID, "schema": SCHEMA_VERSION,
            "contract": "global-country-source-coverage-matrix", "generated_at": _now(),
            "country_count": len(rows), "source_count": len(columns), "columns": columns, "rows": rows,
            "summary": matrix_summary,
            "filters": {"region": region or None, "source": source_id or None, "state": state or None, "limit": max(1,min(int(limit),60)), "offset": max(0,int(offset))},
            "boundaries": [
                "Matrix cells distinguish geographic eligibility from observed country-linked records.",
                "Contract-only eligibility is not presented as verified record availability.",
                "Event-driven zero-record states do not prove absence of the underlying condition.",
            ],
        }


def public_data_truth(settings: Settings, country_code: str | None = None) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).country(country_code) if country_code else SourceTruthCenter(settings).directory()

def public_data_truth_source(settings: Settings, feed_id: str) -> dict[str, Any]:
    return SourceTruthCenter(settings).source(feed_id)

def public_data_truth_countries(settings: Settings) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).countries()

def public_country_data_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).country(country_code)

def public_country_source_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).country_sources(country_code)

def public_country_indicator_truth(settings: Settings, country_code: str) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).country_indicators(country_code)

def public_coverage_matrix(settings: Settings, **kwargs: Any) -> dict[str, Any]:
    return GlobalCountryDataTruth(settings).matrix(**kwargs)
