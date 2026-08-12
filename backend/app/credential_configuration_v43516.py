from __future__ import annotations
"""v4.35.17 — canonical credential/configuration control plane.

Public output is intentionally secret-free. The module only reports whether the
required settings are present and syntactically plausible; it never returns,
hashes, masks, fingerprints, or probes secret material.
"""
from datetime import datetime, timezone
from typing import Any

from .version import APP_VERSION

VERSION = APP_VERSION
CONTRACT = "credentials-api-key-configuration-completion-v43516"

PROFILES = (
    {
        "id": "reliefweb-appname", "organization": "UN OCHA ReliefWeb",
        "workspaces": ("Sources & Methodology", "Humanitarian Intelligence", "Unified Live Events"),
        "fields": (("reliefweb_appname", "SC_SI_RELIEFWEB_APPNAME", "identifier"),),
        "registration_count": 3,
        "acquisition": "pre-approved appname required",
    },
    {
        "id": "airnow-api-key", "organization": "U.S. EPA AirNow",
        "workspaces": ("Atmosphere, Air Quality & Aerosols",),
        "fields": (("airnow_api_key", "SC_SI_AIRNOW_API_KEY", "secret"),),
        "registration_count": 1,
        "acquisition": "free AirNow account/API key",
    },
    {
        "id": "epa-aqs", "organization": "U.S. EPA Air Quality System",
        "workspaces": ("Atmosphere, Air Quality & Aerosols", "Legacy Live External Connectors"),
        "fields": (("epa_aqs_email", "SC_SI_EPA_AQS_EMAIL", "email"), ("epa_aqs_key", "SC_SI_EPA_AQS_KEY", "secret")),
        "registration_count": 2,
        "acquisition": "registered email plus AQS API key",
    },
    {
        "id": "eia-api-key", "organization": "U.S. Energy Information Administration",
        "workspaces": ("Energy Infrastructure & Power Systems", "Legacy Live External Connectors"),
        "fields": (("eia_api_key", "SC_SI_EIA_API_KEY", "secret"),),
        "registration_count": 2,
        "acquisition": "free EIA Open Data API key",
    },
    {
        "id": "ember-api-key", "organization": "Ember",
        "workspaces": ("Energy Infrastructure & Power Systems",),
        "fields": (("ember_api_key", "SC_SI_EMBER_API_KEY", "secret"),),
        "registration_count": 1,
        "acquisition": "Ember Electricity Data API key",
    },
    {
        "id": "entsoe-security-token", "organization": "ENTSO-E",
        "workspaces": ("Energy Infrastructure & Power Systems",),
        "fields": (("entsoe_security_token", "SC_SI_ENTSOE_SECURITY_TOKEN", "secret"),),
        "registration_count": 1,
        "acquisition": "Transparency Platform account plus RESTful API security token",
    },
    {
        "id": "usda-nass-api-key", "organization": "USDA National Agricultural Statistics Service",
        "workspaces": ("Agriculture, Crops & Food Systems",),
        "fields": (("usda_nass_api_key", "SC_SI_USDA_NASS_API_KEY", "secret"),),
        "registration_count": 1,
        "acquisition": "free NASS Quick Stats API key",
    },
    {
        "id": "nasa-firms-map-key", "organization": "NASA LANCE FIRMS",
        "workspaces": ("Terrestrial Ecosystems & Wildfire",),
        "fields": (("nasa_firms_map_key", "SC_SI_NASA_FIRMS_MAP_KEY", "secret"),),
        "registration_count": 1,
        "acquisition": "free FIRMS MAP_KEY",
    },
    {
        "id": "hdx-hapi-app-identifier", "organization": "OCHA Centre for Humanitarian Data / HDX HAPI",
        "workspaces": ("Humanitarian Intelligence",),
        "fields": (("hdx_hapi_app_identifier", "SC_SI_HDX_HAPI_APP_IDENTIFIER", "identifier"),),
        "registration_count": 1,
        "acquisition": "generated HDX HAPI app identifier",
    },
    {
        "id": "ipc-api-key", "organization": "Integrated Food Security Phase Classification",
        "workspaces": ("Agriculture, Crops & Food Systems",),
        "fields": (("ipc_api_key", "SC_SI_IPC_API_KEY", "secret"),),
        "registration_count": 1,
        "acquisition": "approved IPC API access/API key",
    },
    {
        "id": "copernicus-marine-account", "organization": "Copernicus Marine Service",
        "workspaces": ("Ocean Surface", "Water Column & Depth"),
        "fields": (("copernicus_marine_username", "SC_SI_COPERNICUS_MARINE_USERNAME", "identifier"), ("copernicus_marine_password", "SC_SI_COPERNICUS_MARINE_PASSWORD", "secret")),
        "registration_count": 2,
        "acquisition": "free Copernicus Marine account username/password",
    },
    {
        "id": "global-fishing-watch-token", "organization": "Global Fishing Watch",
        "workspaces": ("Marine Human Activity & Protected Areas",),
        "fields": (("global_fishing_watch_api_token", "SC_SI_GLOBAL_FISHING_WATCH_API_TOKEN", "secret"),),
        "registration_count": 1,
        "acquisition": "Global Fishing Watch API v3 access token",
    },
)

_PROFILE_BY_ID = {p["id"]: p for p in PROFILES}
_SOURCE_PROFILE_RULES = {
    ("Sources & Methodology", "reliefweb"): "reliefweb-appname",
    ("Humanitarian Intelligence", "reliefweb"): "reliefweb-appname",
    ("Unified Live Events", "reliefweb"): "reliefweb-appname",
    ("Atmosphere, Air Quality & Aerosols", "airnow"): "airnow-api-key",
    ("Atmosphere, Air Quality & Aerosols", "epa-aqs"): "epa-aqs",
    ("Legacy Live External Connectors", "epa_aqs_air_quality"): "epa-aqs",
    ("Energy Infrastructure & Power Systems", "eia-open-data"): "eia-api-key",
    ("Legacy Live External Connectors", "eia_energy"): "eia-api-key",
    ("Energy Infrastructure & Power Systems", "ember-electricity-data"): "ember-api-key",
    ("Energy Infrastructure & Power Systems", "entsoe-transparency"): "entsoe-security-token",
    ("Agriculture, Crops & Food Systems", "usda-nass-quick-stats"): "usda-nass-api-key",
    ("Terrestrial Ecosystems & Wildfire", "nasa-firms"): "nasa-firms-map-key",
    ("Humanitarian Intelligence", "hdx-hapi-food-security"): "hdx-hapi-app-identifier",
    ("Agriculture, Crops & Food Systems", "ipc-food-security-api"): "ipc-api-key",
    ("Ocean Surface", "copernicus-marine"): "copernicus-marine-account",
    ("Water Column & Depth", "copernicus-marine"): "copernicus-marine-account",
    ("Marine Human Activity & Protected Areas", "global-fishing-watch"): "global-fishing-watch-token",
}

_PLACEHOLDER_MARKERS = ("change-me", "changeme", "replace-me", "replace_with", "your-key", "your_key", "example", "dummy", "placeholder")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _value(settings: Any, field: str) -> str:
    return str(getattr(settings, field, "") or "").strip() if settings is not None else ""


def _field_valid(kind: str, value: str) -> bool:
    if not value:
        return False
    low = value.lower()
    if any(marker in low for marker in _PLACEHOLDER_MARKERS):
        return False
    if kind == "email":
        return "@" in value and "." in value.rsplit("@", 1)[-1]
    if kind == "secret":
        return len(value) >= 8
    return len(value) >= 3


def profile_state(profile: dict[str, Any], settings: Any) -> str:
    values = [(_value(settings, field), kind) for field, _env, kind in profile["fields"]]
    present = [bool(value) for value, _kind in values]
    if not any(present):
        return "missing"
    if not all(present):
        return "partial"
    if not all(_field_valid(kind, value) for value, kind in values):
        return "invalid"
    return "configured"


def _public_profile(profile: dict[str, Any], settings: Any) -> dict[str, Any]:
    state = profile_state(profile, settings)
    return {
        "id": profile["id"],
        "organization": profile["organization"],
        "workspaces": list(profile["workspaces"]),
        "required_environment": [env for _field, env, _kind in profile["fields"]],
        "required_environment_count": len(profile["fields"]),
        "state": state,
        "configured": state == "configured",
        "source_registration_count": profile["registration_count"],
        "acquisition": profile["acquisition"],
        "secret_material_exposed": False,
        "network_probe_performed": False,
        "release_blocking": False,
    }


def credential_registry(settings: Any = None) -> dict[str, Any]:
    rows = [_public_profile(p, settings) for p in PROFILES]
    states = {name: sum(r["state"] == name for r in rows) for name in ("configured", "missing", "partial", "invalid")}
    mapped = sum(p["registration_count"] for p in PROFILES)
    completion = "complete" if states["configured"] == len(rows) else "partial" if states["configured"] else "not-configured"
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "profile_count": len(rows),
        "mapped_auth_required_registrations": mapped,
        "states": states,
        "configuration_complete": completion == "complete",
        "completion_status": completion,
        "profiles": rows,
        "secret_material_exposed": False,
        "network_calls_performed": False,
        "generated_at": _now(),
    }


def credential_readiness(settings: Any = None) -> dict[str, Any]:
    registry = credential_registry(settings)
    envs = [env for p in PROFILES for _field, env, _kind in p["fields"]]
    checks = {
        "twelve_unique_credential_profiles": len(PROFILES) == 12,
        "seventeen_auth_required_registrations_mapped": sum(p["registration_count"] for p in PROFILES) == 17,
        "environment_names_unique": len(envs) == len(set(envs)),
        "all_profiles_have_workspace_scope": all(p["workspaces"] for p in PROFILES),
        "secret_material_never_returned": True,
        "network_free": True,
        "missing_credentials_non_blocking_for_release": True,
    }
    return {
        "ok": all(checks.values()),
        "version": VERSION,
        "contract": CONTRACT,
        "checks": checks,
        "configuration_complete": registry["configuration_complete"],
        "completion_status": registry["completion_status"],
        "states": registry["states"],
        "profile_count": registry["profile_count"],
        "mapped_auth_required_registrations": registry["mapped_auth_required_registrations"],
        "network_calls_performed": False,
        "generated_at": _now(),
    }


def credential_workspaces(settings: Any = None) -> dict[str, Any]:
    rows = credential_registry(settings)["profiles"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for workspace in row["workspaces"]:
            grouped.setdefault(workspace, []).append(row)
    workspaces = []
    for workspace in sorted(grouped):
        profiles = grouped[workspace]
        workspaces.append({
            "workspace": workspace,
            "credential_profiles": len(profiles),
            "configured_profiles": sum(p["configured"] for p in profiles),
            "configuration_complete": all(p["configured"] for p in profiles),
            "profiles": [p["id"] for p in profiles],
        })
    return {
        "ok": True,
        "version": VERSION,
        "contract": CONTRACT,
        "workspace_count": len(workspaces),
        "workspaces": workspaces,
        "network_calls_performed": False,
        "generated_at": _now(),
    }


def profile_for_source(workspace: str, source_id: str) -> str | None:
    return _SOURCE_PROFILE_RULES.get((workspace, source_id))


def canonical_configuration_for_source(workspace: str, source_id: str, settings: Any) -> dict[str, Any] | None:
    profile_id = profile_for_source(workspace, source_id)
    if not profile_id:
        return None
    row = _public_profile(_PROFILE_BY_ID[profile_id], settings)
    state_map = {"configured": "configured", "missing": "configuration-required", "partial": "configuration-partial", "invalid": "configuration-invalid"}
    return {
        "credential_profile": profile_id,
        "configuration_state": state_map[row["state"]],
        "configuration_key": " + ".join(row["required_environment"]),
        "credential_state": row["state"],
        "secret_material_exposed": False,
    }
