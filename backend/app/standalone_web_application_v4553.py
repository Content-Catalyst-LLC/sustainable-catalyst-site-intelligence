from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

from .version import APP_VERSION

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "standalone_web_application_registry_v4553.json"
SCHEMA = "sc-site-intelligence-standalone-web-application-registry/1.0"


def _registry() -> dict[str, Any]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if data.get("version") != APP_VERSION or data.get("schema") != SCHEMA:
        raise ValueError("standalone web application registry mismatch")
    return data


def _web_origin() -> str:
    return (os.getenv("SC_SI_WEB_APP_URL") or _registry()["application_origin"]).rstrip("/")


def _api_origin() -> str:
    return (os.getenv("SC_SI_PUBLIC_API_URL") or _registry()["api_origin"]).rstrip("/")


def manifest() -> dict[str, Any]:
    data = deepcopy(_registry())
    data["application_origin"] = _web_origin()
    data["api_origin"] = _api_origin()
    return {"ok": True, **data}


def route_manifest() -> dict[str, Any]:
    r = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "application_origin": _web_origin(),
        "count": len(r["routes"]),
        "routes": deepcopy(r["routes"]),
        "routing_authority": "standalone-web-application",
        "query_string_view_routing_authoritative": False,
    }


def config_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "application_origin": _web_origin(),
        "api_origin": _api_origin(),
        "api_transport": {
            "credentials": "include",
            "public_reads": True,
            "client_supplied_backend_urls_allowed": False,
            "api_origin_configurable_at_deploy": True,
        },
        "cors": {
            "required_origin": _web_origin(),
            "wildcard_required": False,
            "credentials_supported": True,
        },
        "wordpress": {
            "runtime_dependency": False,
            "api_proxy_required": False,
            "role": "public-site-launch-bridge",
        },
    }


def context_contract() -> dict[str, Any]:
    propagated = ["country", "dossiers", "economics", "law", "science", "earth", "humanitarian", "resources", "research"]
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": "sc-site-intelligence-web-context/1.0",
        "canonical_fields": ["country_code", "country_name", "route_id", "research_context_id"],
        "default_country_code": "KEN",
        "persistence": {"url_path": True, "session_storage": True, "local_storage_authoritative": False},
        "propagates_to": propagated,
        "country_context_is_decorative": False,
        "country_context_drives_workspace_requests": True,
    }


def wordpress_decoupling_contract() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "wordpress_role": "public-site-launch-bridge",
        "standalone_boot_requires_wordpress": False,
        "standalone_routing_requires_wordpress": False,
        "standalone_state_requires_wordpress": False,
        "standalone_api_transport_requires_wordpress": False,
        "wordpress_may_link_to_app": True,
        "wordpress_may_embed_selected_public_views": True,
        "wordpress_is_application_authority": False,
        "wordpress_is_state_authority": False,
        "wordpress_is_api_proxy_authority": False,
    }


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "preserves": [
            "v4.55.2-advanced-domain-intelligence",
            "v4.55.1-workspace-runtime-repair",
            "legacy-fastapi-served-/app/-compatibility",
        ],
        "legacy_app_path_deprecated": True,
        "legacy_app_path_removed": False,
        "standalone_web_is_preferred": True,
        "wordpress_runtime_dependency": False,
    }
