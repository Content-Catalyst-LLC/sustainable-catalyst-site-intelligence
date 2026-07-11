from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping
from uuid import uuid4

from .version import APP_VERSION

VERSION = APP_VERSION
SCHEMA_VERSION = "sc-saved-view/1.0"
LEGACY_SCHEMA_VERSIONS = ("sc-saved-view/0.9",)
STORAGE_KEY = "sc_site_intelligence_saved_views_v1"
MAX_MANIFEST_BYTES = 65536
MAX_NAME_LENGTH = 120
MAX_SAVED_VIEWS = 50

ALLOWED_VIEWS: dict[str, dict[str, Any]] = {
    "overview": {
        "label": "Overview",
        "description": "Live map, imagery date, public events, and country context.",
        "state_keys": ["country", "imageryLayer", "imageryDate", "mapLat", "mapLng", "mapZoom"],
    },
    "earth": {
        "label": "Earth Observation",
        "description": "Imagery layer, dates, opacity, swipe position, and map viewport.",
        "state_keys": ["earthLayer", "dateA", "dateB", "opacity", "swipe", "mapLat", "mapLng", "mapZoom"],
    },
    "country": {
        "label": "Country Intelligence",
        "description": "Selected country, trend, and map viewport.",
        "state_keys": ["country", "trend", "mapLat", "mapLng", "mapZoom"],
    },
    "events": {
        "label": "Live Event Intelligence",
        "description": "Event window, category, source, country filter, and map viewport.",
        "state_keys": ["eventDays", "eventCategory", "eventSource", "eventCountry", "mapLat", "mapLng", "mapZoom"],
    },
    "compare": {
        "label": "Comparative Intelligence",
        "description": "Country pair, active comparison view, indicator, trend, and map viewport.",
        "state_keys": ["country", "compare", "compareView", "indicator", "trend", "mapLat", "mapLng", "mapZoom"],
    },
    "thematic": {
        "label": "Thematic Intelligence",
        "description": "Dashboard, country, event window, Earth layer, trend, and map viewport.",
        "state_keys": ["dashboard", "country", "thematicDays", "thematicLayer", "thematicTrend", "mapLat", "mapLng", "mapZoom"],
    },
    "briefing": {
        "label": "Public Briefing Studio",
        "description": "Brief type and public investigation parameters.",
        "state_keys": ["briefType", "type", "country", "compare", "days", "event_id", "dashboard_id", "layer_id", "date_a", "date_b", "latitude", "longitude", "zoom", "opacity"],
    },
    "sources": {
        "label": "Source and Methodology Studio",
        "description": "Source record and public registry filters.",
        "state_keys": ["source", "domain", "state", "feature", "query"],
    },
}

THEMATIC_DASHBOARDS = {
    "climate-environment",
    "human-development",
    "human-security",
    "infrastructure",
}
EARTH_LAYER_IDS = {
    "true-color",
    "land-surface-temperature",
    "fires-thermal-anomalies",
    "vegetation-index",
    "precipitation-rate",
    "snow-cover",
    "nighttime-lights",
    "aerosol-optical-depth",
}
COMPARE_VIEWS = {"table", "chart", "map", "brief", "export"}
SOURCE_STATES = {"live", "cached", "stale", "temporarily-unavailable", "experimental", "disabled"}
BRIEF_TYPES = {"country", "comparison", "event", "earth", "thematic"}
ISO3_RE = re.compile(r"^[A-Z]{3}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|password|passwd|secret|token|authorization|cookie|session|private[_-]?url|stack[_-]?trace|environment|diagnostics)",
    re.IGNORECASE,
)


class SavedViewError(ValueError):
    """Raised when a saved-view manifest cannot be accepted safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, *, field: str) -> str:
    if value in (None, ""):
        return _utc_now()
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SavedViewError(f"{field} must be an ISO 8601 timestamp.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bounded_text(value: Any, *, field: str, max_length: int, allow_empty: bool = False) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text and not allow_empty:
        raise SavedViewError(f"{field} is required.")
    if len(text) > max_length:
        raise SavedViewError(f"{field} must be {max_length} characters or fewer.")
    return text


def _safe_slug(value: Any, *, field: str, allow_empty: bool = True) -> str:
    text = str(value or "").strip().lower()
    if not text and allow_empty:
        return ""
    if not SLUG_RE.fullmatch(text):
        raise SavedViewError(f"{field} contains unsupported characters.")
    return text


def _country(value: Any, *, field: str, allow_empty: bool = True) -> str:
    text = str(value or "").strip().upper()
    if not text and allow_empty:
        return ""
    if not ISO3_RE.fullmatch(text):
        raise SavedViewError(f"{field} must be a three-letter ISO-style country code.")
    return text


def _integer(value: Any, *, field: str, minimum: int, maximum: int, allow_empty: bool = True) -> str:
    if value in (None, "") and allow_empty:
        return ""
    try:
        number = int(str(value))
    except (TypeError, ValueError) as exc:
        raise SavedViewError(f"{field} must be an integer.") from exc
    if not minimum <= number <= maximum:
        raise SavedViewError(f"{field} must be between {minimum} and {maximum}.")
    return str(number)


def _float(value: Any, *, field: str, minimum: float, maximum: float, allow_empty: bool = True) -> str:
    if value in (None, "") and allow_empty:
        return ""
    try:
        number = float(str(value))
    except (TypeError, ValueError) as exc:
        raise SavedViewError(f"{field} must be numeric.") from exc
    if not minimum <= number <= maximum:
        raise SavedViewError(f"{field} must be between {minimum} and {maximum}.")
    rendered = f"{number:.6f}".rstrip("0").rstrip(".")
    return rendered or "0"


def _date(value: Any, *, field: str, allow_empty: bool = True) -> str:
    text = str(value or "").strip()
    if not text and allow_empty:
        return ""
    if not DATE_RE.fullmatch(text):
        raise SavedViewError(f"{field} must use YYYY-MM-DD format.")
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise SavedViewError(f"{field} is not a valid calendar date.") from exc
    return text


def _scan_sensitive(value: Any, path: str = "manifest") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if SENSITIVE_KEY_RE.search(key_text):
                issues.append(f"Sensitive field is not allowed: {child_path}")
            issues.extend(_scan_sensitive(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_sensitive(child, f"{path}[{index}]"))
    return issues


def _migrate_legacy(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], str | None, list[str]]:
    migrated = deepcopy(dict(manifest))
    schema = str(migrated.get("schema") or "")
    warnings: list[str] = []
    if schema == SCHEMA_VERSION:
        return migrated, None, warnings
    if schema not in LEGACY_SCHEMA_VERSIONS:
        raise SavedViewError(f"Unsupported saved-view schema: {schema or 'missing'}.")

    migrated_from = schema
    if "view" not in migrated and "route" in migrated:
        migrated["view"] = migrated.pop("route")
    if "state" not in migrated and isinstance(migrated.get("params"), Mapping):
        migrated["state"] = dict(migrated.pop("params"))
    if "name" not in migrated and "title" in migrated:
        migrated["name"] = migrated.pop("title")
    if "created_at" not in migrated and "saved_at" in migrated:
        migrated["created_at"] = migrated.pop("saved_at")
    migrated["schema"] = SCHEMA_VERSION
    warnings.append(f"Manifest migrated from {migrated_from} to {SCHEMA_VERSION}.")
    return migrated, migrated_from, warnings


def _normalize_state(view: str, state: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    allowed = set(ALLOWED_VIEWS[view]["state_keys"])
    normalized: dict[str, str] = {}
    warnings: list[str] = []

    for raw_key, raw_value in state.items():
        key = str(raw_key)
        if key not in allowed:
            warnings.append(f"Unsupported state field removed: {key}.")
            continue
        if raw_value in (None, ""):
            continue

        if key in {"country", "compare", "eventCountry"}:
            value = _country(raw_value, field=key)
        elif key in {"dateA", "dateB", "imageryDate", "date_a", "date_b"}:
            value = _date(raw_value, field=key)
        elif key in {"eventDays", "thematicDays", "days"}:
            value = _integer(raw_value, field=key, minimum=1, maximum=365)
        elif key == "opacity" and view == "briefing":
            value = _float(raw_value, field=key, minimum=0, maximum=1)
        elif key in {"opacity", "swipe"}:
            value = _integer(raw_value, field=key, minimum=0, maximum=100)
        elif key in {"mapZoom", "zoom"}:
            value = _float(raw_value, field=key, minimum=0, maximum=20)
        elif key in {"mapLat", "latitude"}:
            value = _float(raw_value, field=key, minimum=-90, maximum=90)
        elif key in {"mapLng", "longitude"}:
            value = _float(raw_value, field=key, minimum=-180, maximum=180)
        elif key in {"dashboard", "dashboard_id"}:
            value = _safe_slug(raw_value, field=key, allow_empty=False)
            if value not in THEMATIC_DASHBOARDS:
                raise SavedViewError(f"Unsupported thematic dashboard: {value}.")
        elif key in {"earthLayer", "thematicLayer", "imageryLayer", "layer_id"}:
            value = _safe_slug(raw_value, field=key, allow_empty=False)
            if value not in EARTH_LAYER_IDS:
                raise SavedViewError(f"Unsupported Earth-observation layer: {value}.")
        elif key == "compareView":
            value = _safe_slug(raw_value, field=key, allow_empty=False)
            if value not in COMPARE_VIEWS:
                raise SavedViewError(f"Unsupported comparison view: {value}.")
        elif key == "state" and view == "sources":
            value = _safe_slug(raw_value, field=key, allow_empty=False)
            if value not in SOURCE_STATES:
                raise SavedViewError(f"Unsupported source state: {value}.")
        elif key in {"briefType", "type"}:
            value = _safe_slug(raw_value, field=key, allow_empty=False)
            if value not in BRIEF_TYPES:
                raise SavedViewError(f"Unsupported brief type: {value}.")
        elif key == "query":
            value = _bounded_text(raw_value, field=key, max_length=160, allow_empty=True)
        elif key == "event_id":
            value = _bounded_text(raw_value, field=key, max_length=180, allow_empty=True)
        else:
            value = _safe_slug(raw_value, field=key, allow_empty=True)

        if value != "":
            normalized[key] = value

    if view in {"country", "compare", "thematic", "briefing"} and "country" not in normalized:
        normalized["country"] = "KEN"
        warnings.append("Country was missing and defaulted to KEN.")
    if view == "compare" and "compare" not in normalized:
        normalized["compare"] = "GHA"
        warnings.append("Comparison country was missing and defaulted to GHA.")
    if view == "compare" and normalized.get("country") == normalized.get("compare"):
        raise SavedViewError("Primary and comparison countries must be different.")
    if view == "thematic" and "dashboard" not in normalized:
        normalized["dashboard"] = "climate-environment"
        warnings.append("Dashboard was missing and defaulted to climate-environment.")
    if view == "earth":
        normalized.setdefault("earthLayer", "true-color")
        normalized.setdefault("opacity", "72")
        normalized.setdefault("swipe", "50")
        if normalized.get("dateA") and normalized.get("dateB") and normalized["dateA"] > normalized["dateB"]:
            raise SavedViewError("dateA must not be later than dateB.")
    if view == "briefing" and normalized.get("date_a") and normalized.get("date_b") and normalized["date_a"] > normalized["date_b"]:
        raise SavedViewError("date_a must not be later than date_b.")
    if view == "briefing":
        brief_type = normalized.get("briefType") or normalized.get("type") or "country"
        normalized["briefType"] = brief_type
        normalized["type"] = brief_type

    return normalized, warnings


def normalize_manifest(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], list[str], str | None]:
    raw_json = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
    if len(raw_json.encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise SavedViewError(f"Manifest exceeds the {MAX_MANIFEST_BYTES}-byte limit.")

    sensitive = _scan_sensitive(manifest)
    if sensitive:
        raise SavedViewError(sensitive[0])

    migrated, migrated_from, warnings = _migrate_legacy(manifest)
    name = _bounded_text(migrated.get("name"), field="name", max_length=MAX_NAME_LENGTH)
    view = _safe_slug(migrated.get("view"), field="view", allow_empty=False)
    if view not in ALLOWED_VIEWS:
        raise SavedViewError(f"Unsupported saved view: {view}.")

    state_value = migrated.get("state", {})
    if not isinstance(state_value, Mapping):
        raise SavedViewError("state must be an object.")
    state, state_warnings = _normalize_state(view, state_value)
    warnings.extend(state_warnings)

    manifest_id = str(migrated.get("id") or "").strip()
    if manifest_id:
        if not re.fullmatch(r"[A-Za-z0-9._:-]{6,128}", manifest_id):
            raise SavedViewError("id contains unsupported characters.")
    else:
        manifest_id = f"sv-{uuid4().hex}"
        warnings.append("A saved-view ID was generated.")

    normalized = {
        "schema": SCHEMA_VERSION,
        "application_version": _bounded_text(
            migrated.get("application_version") or VERSION,
            field="application_version",
            max_length=32,
        ),
        "id": manifest_id,
        "name": name,
        "view": view,
        "state": state,
        "created_at": _parse_timestamp(migrated.get("created_at"), field="created_at"),
        "updated_at": _parse_timestamp(
            migrated.get("updated_at") or migrated.get("created_at"),
            field="updated_at",
        ),
    }
    return normalized, warnings, migrated_from


def validate_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        return {
            "ok": True,
            "valid": False,
            "schema": SCHEMA_VERSION,
            "errors": ["Request body must be a saved-view object."],
            "warnings": [],
            "manifest": None,
            "persisted": False,
        }
    try:
        normalized, warnings, migrated_from = normalize_manifest(manifest)
    except SavedViewError as exc:
        return {
            "ok": True,
            "valid": False,
            "schema": SCHEMA_VERSION,
            "errors": [str(exc)],
            "warnings": [],
            "manifest": None,
            "persisted": False,
        }
    return {
        "ok": True,
        "valid": True,
        "schema": SCHEMA_VERSION,
        "errors": [],
        "warnings": warnings,
        "migrated_from": migrated_from,
        "manifest": normalized,
        "persisted": False,
    }


def schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": SCHEMA_VERSION,
        "storage_key": STORAGE_KEY,
        "storage": "browser-localStorage",
        "max_saved_views": MAX_SAVED_VIEWS,
        "max_manifest_bytes": MAX_MANIFEST_BYTES,
        "allowed_views": [
            {
                "id": view_id,
                **details,
            }
            for view_id, details in ALLOWED_VIEWS.items()
        ],
        "required_fields": ["schema", "application_version", "id", "name", "view", "state", "created_at"],
        "privacy": {
            "server_persistence": False,
            "cross_device_sync": False,
            "accounts_required": False,
            "shared_urls_contain_public_state_only": True,
            "sensitive_fields_allowed": False,
        },
    }


def migrations_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "current_schema": SCHEMA_VERSION,
        "migrations": [
            {
                "from": "sc-saved-view/0.9",
                "to": SCHEMA_VERSION,
                "rules": [
                    "route becomes view",
                    "params becomes state",
                    "title becomes name",
                    "saved_at becomes created_at",
                    "unsupported state keys are removed",
                ],
            }
        ],
        "unsupported_schemas_are_rejected": True,
        "persistence": "none",
    }


def diagnostics() -> dict[str, Any]:
    issues: list[str] = []
    for view_id, record in ALLOWED_VIEWS.items():
        keys = record.get("state_keys") or []
        if not keys:
            issues.append(f"{view_id} has no registered public state keys")
        if len(keys) != len(set(keys)):
            issues.append(f"{view_id} contains duplicate state keys")
    sensitive_key_overlap = sorted(
        key
        for record in ALLOWED_VIEWS.values()
        for key in record.get("state_keys", [])
        if SENSITIVE_KEY_RE.search(key)
    )
    if sensitive_key_overlap:
        issues.append("Sensitive-looking state keys are registered: " + ", ".join(sensitive_key_overlap))

    return {
        "ok": not issues,
        "version": VERSION,
        "schema": SCHEMA_VERSION,
        "storage_key": STORAGE_KEY,
        "registered_views": len(ALLOWED_VIEWS),
        "migration_count": len(LEGACY_SCHEMA_VERSIONS),
        "issues": issues,
        "checks": {
            "server_persistence_disabled": True,
            "sensitive_field_scan_enabled": True,
            "unsupported_state_fields_removed": True,
            "unsupported_views_rejected": True,
            "invalid_country_codes_rejected": True,
            "manifest_size_limited": True,
        },
        "public_boundary": "Validation is structural only. The backend does not store imported or validated saved views.",
    }
