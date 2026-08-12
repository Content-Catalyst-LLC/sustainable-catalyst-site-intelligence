from __future__ import annotations

"""Site Intelligence v4.35.22 — Palestine official open-data connector extension."""

from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlencode

from .version import APP_VERSION
from . import authoritative_connectors_v43515 as prior
from .authoritative_connectors_v4355 import _request_json

VERSION = APP_VERSION
CONTRACT = "palestine-official-open-data-connector-v43521"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout(settings: Any) -> int:
    return int(getattr(settings, "external_request_timeout_seconds", 8)) if settings is not None else 8


def _setting(settings: Any, name: str, default: str = "") -> str:
    value = str(getattr(settings, name, "") or "").strip() if settings is not None else ""
    return value or default


NEW_CONNECTORS = (
    {
        "id": "palestine-open-data-ckan",
        "title": "Palestine Open Data Portal CKAN API",
        "organization": "Palestine Open Data Portal / Palestinian public institutions",
        "workspace": "Country Intelligence / Palestine",
        "mode": "DISCOVERY",
        "authentication": "public",
        "boundary": (
            "Palestine Open Data Portal records are official/public-institution dataset discovery metadata. "
            "Dataset presence is not a current-condition observation; resource scope, reference period, methodology, "
            "licensing and publishing institution remain attached before substantive use."
        ),
    },
)

CONNECTORS = tuple(prior.CONNECTORS) + NEW_CONNECTORS
for _name in [n for n in dir(prior) if not n.startswith("_") and callable(getattr(prior, n)) and n not in {"connector_catalog", "connector_readiness"}]:
    if _name not in globals():
        globals()[_name] = getattr(prior, _name)


def connector_catalog(settings: Any = None) -> dict[str, Any]:
    rows = [dict(x) for x in prior.connector_catalog(settings)["connectors"]]
    for connector in NEW_CONNECTORS:
        row = dict(connector)
        row.update({"credential_configured": True, "configuration_key": None, "network_check_performed": False})
        rows.append(row)
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "connector_count": len(rows),
        "live_connector_count": sum(x["mode"] == "LIVE" for x in rows),
        "discovery_connector_count": sum(x["mode"] == "DISCOVERY" for x in rows),
        "auth_required_connector_count": sum(x["mode"] == "AUTH_REQUIRED" for x in rows),
        "configured_auth_required_connector_count": sum(x["mode"] == "AUTH_REQUIRED" and x.get("credential_configured") for x in rows),
        "v43521_connector_count": len(NEW_CONNECTORS),
        "connectors": rows,
        "principles": [
            "Palestine Open Data Portal is treated as official/public-institution discovery evidence, not as a live operational feed.",
            "PCBS remains the primary Palestinian statistical authority for exact supported concepts.",
            "HDX/OCHA humanitarian discovery and operational evidence remain semantically separate from Palestinian official datasets.",
            "Upstream availability remains non-blocking for deployment.",
        ],
        "generated_at": _now(),
    }


def connector_readiness(settings: Any = None) -> dict[str, Any]:
    catalog = connector_catalog(settings)
    ids = {x["id"] for x in catalog["connectors"]}
    checks = {
        "fifty_one_interfaces_registered": catalog["connector_count"] == 51,
        "thirty_one_live": catalog["live_connector_count"] == 31,
        "twelve_discovery": catalog["discovery_connector_count"] == 12,
        "eight_auth_required": catalog["auth_required_connector_count"] == 8,
        "palestine_open_data_present": "palestine-open-data-ckan" in ids,
        "network_free": True,
        "upstream_health_non_blocking": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "network_calls_performed": False,
        "checks": checks,
        "generated_at": _now(),
    }


def palestine_open_data_search(settings: Any, *, query: str = "", rows: int = 20) -> dict[str, Any]:
    q = str(query or "").strip()
    if len(q) > 160 or (q and not re.fullmatch(r"[\w\s.,'()&:/+\-]+", q, re.UNICODE)):
        raise ValueError("query is invalid")
    rows = int(rows)
    if not 1 <= rows <= 50:
        raise ValueError("rows must be between 1 and 50")
    base = _setting(settings, "palestine_open_data_base_url", "https://opendata.ps/api/3/action").rstrip("/")
    params = {"rows": rows}
    if q:
        params["q"] = q
    endpoint = f"{base}/package_search?{urlencode(params)}"
    payload = _request_json(endpoint, timeout=_timeout(settings))
    return {
        "ok": True,
        "version": VERSION,
        "connector_id": "palestine-open-data-ckan",
        "mode": "DISCOVERY",
        "query": {"q": q or None, "rows": rows},
        "data": payload,
        "provenance": {
            "organization": "Palestine Open Data Portal / Palestinian public institutions",
            "endpoint": endpoint,
            "retrieved_at": _now(),
        },
        "boundary": NEW_CONNECTORS[0]["boundary"],
    }
