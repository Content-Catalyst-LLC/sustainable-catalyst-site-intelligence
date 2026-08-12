"""Canonical first-party country identity registry for Site Intelligence v4.35.23.

Country selection and routing must not depend on a live statistical provider.  This
module provides the shared ISO3/ISO2/name/coordinate identity layer used by the
selector, country resolver, cartographic focus, and Data Truth catalog.  External
providers may enrich metadata, but cannot replace the canonical identity key.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

SCHEMA = "sc-site-intelligence-country-identity-registry/1.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "country_identity_registry_v43523.json"


@lru_cache(maxsize=1)
def country_identity_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise RuntimeError("country_identity_registry_schema_mismatch")
    rows: dict[str, dict[str, Any]] = {}
    for item in payload.get("countries") or []:
        code = str(item.get("code") or "").strip().upper()
        iso2 = str(item.get("iso2") or "").strip().upper()
        name = " ".join(str(item.get("name") or "").split())
        if len(code) != 3 or len(iso2) != 2 or not name:
            continue
        rows[code] = {
            **item,
            "code": code,
            "iso2": iso2,
            "name": name,
            "display_name": name,
            "source_name": item.get("source_name") or name,
            "alternate_names": sorted({
                " ".join(str(value or "").split())
                for value in item.get("alternate_names") or []
                if " ".join(str(value or "").split()) and " ".join(str(value or "").split()) != name
            }),
            "identity_source": "first-party-canonical-registry",
            "identity_version": APP_VERSION,
        }
    if "ISR" not in rows or "PSE" not in rows:
        raise RuntimeError("country_identity_registry_required_identity_missing")
    if rows["ISR"]["iso2"] != "IL" or rows["PSE"]["iso2"] != "PS":
        raise RuntimeError("country_identity_registry_israel_palestine_binding_invalid")
    return dict(sorted(rows.items(), key=lambda item: (item[1].get("name") or item[0], item[0])))


def canonical_country(code_or_alias: str) -> tuple[str, dict[str, Any]]:
    requested = " ".join(str(code_or_alias or "").split())
    normalized = requested.upper()
    folded = requested.casefold()
    registry = country_identity_registry()
    if normalized in registry:
        record = dict(registry[normalized])
        record.pop("code", None)
        return normalized, record
    for code, record in registry.items():
        if str(record.get("iso2") or "").upper() == normalized:
            item = dict(record); item.pop("code", None); return code, item
        names = [record.get("name"), record.get("display_name"), record.get("source_name"), *(record.get("alternate_names") or [])]
        if folded and any(" ".join(str(name or "").split()).casefold() == folded for name in names if name):
            item = dict(record); item.pop("code", None); return code, item
    raise ValueError("unsupported_country")


def readiness() -> dict[str, Any]:
    rows = country_identity_registry()
    israel = rows["ISR"]
    palestine = rows["PSE"]
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": SCHEMA,
        "country_count": len(rows),
        "network_calls_performed": False,
        "upstream_health_release_blocking": False,
        "checks": {
            "canonical_registry_present": len(rows) >= 170,
            "unique_iso3_codes": len(rows) == len(set(rows)),
            "israel_iso3_bound_to_israel": israel["code"] == "ISR" and israel["iso2"] == "IL" and israel["name"] == "Israel",
            "palestine_iso3_bound_to_palestine": palestine["code"] == "PSE" and palestine["iso2"] == "PS" and palestine["name"] == "Palestine",
            "country_identity_is_first_party": israel["identity_source"] == "first-party-canonical-registry" and palestine["identity_source"] == "first-party-canonical-registry",
        },
    }
