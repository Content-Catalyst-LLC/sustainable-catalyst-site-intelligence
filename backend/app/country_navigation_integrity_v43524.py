from __future__ import annotations

from typing import Any

from .country_identity_v43523 import country_identity_registry
from .live_country_intelligence import _merge_country_catalogs
from .version import APP_VERSION

CONTRACT = "country-navigation-integrity-palestine-first-v43524"


def readiness() -> dict[str, Any]:
    canonical = country_identity_registry()
    hostile = {
        "ISR": {
            "code": "ISR",
            "iso2": "PS",
            "name": "Palestine",
            "latitude": canonical["PSE"]["latitude"],
            "longitude": canonical["PSE"]["longitude"],
            "income_level": "external-enrichment-test",
            "source": "simulated-external-catalog",
        },
        "PSE": {
            "code": "PSE",
            "iso2": "IL",
            "name": "Israel",
            "latitude": canonical["ISR"]["latitude"],
            "longitude": canonical["ISR"]["longitude"],
            "income_level": "external-enrichment-test",
            "source": "simulated-external-catalog",
        },
    }
    merged = _merge_country_catalogs(canonical, hostile)
    israel = merged["ISR"]
    palestine = merged["PSE"]
    checks = {
        "palestine_identity_survives_external_override": (
            palestine["code"] == "PSE"
            and palestine["iso2"] == "PS"
            and palestine["name"] == "Palestine"
            and float(palestine["latitude"]) == float(canonical["PSE"]["latitude"])
            and float(palestine["longitude"]) == float(canonical["PSE"]["longitude"])
        ),
        "israel_identity_survives_external_override": (
            israel["code"] == "ISR"
            and israel["iso2"] == "IL"
            and israel["name"] == "Israel"
            and float(israel["latitude"]) == float(canonical["ISR"]["latitude"])
            and float(israel["longitude"]) == float(canonical["ISR"]["longitude"])
        ),
        "external_metadata_is_enrichment_only": (
            palestine.get("income_level") == "external-enrichment-test"
            and israel.get("income_level") == "external-enrichment-test"
            and palestine.get("metadata_source") == "simulated-external-catalog"
        ),
        "palestine_and_israel_remain_distinct": (
            (palestine["latitude"], palestine["longitude"]) != (israel["latitude"], israel["longitude"])
            and palestine["iso2"] != israel["iso2"]
        ),
    }
    return {
        "ok": all(checks.values()),
        "version": APP_VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "checks": checks,
        "policy": {
            "selector_identity": "first-party canonical registry",
            "overview_map_focus": "canonical coordinates before upstream evidence",
            "external_country_catalog": "enrichment only; identity and coordinates cannot override canonical values",
            "cross_identity_response": "blocked",
            "palestine_binding": "PSE -> PS -> Palestine",
            "israel_binding": "ISR -> IL -> Israel",
        },
    }
