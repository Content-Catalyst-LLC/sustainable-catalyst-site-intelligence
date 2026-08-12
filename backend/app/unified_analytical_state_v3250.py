"""Unified analytical workspace and cross-view state for Site Intelligence v4.35.16."""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlencode

from .config import Settings
from .data_truth_v32371 import public_data_truth_countries
from .version import APP_VERSION

SCHEMA_VERSION = "sc-site-intelligence-unified-analytical-state/1.0"
RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "unified_analytical_state_policy_v3250.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
CATEGORY_RE = re.compile(r"^[A-Za-z0-9 _.-]{1,80}$")


def _policy() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != APP_VERSION:
        raise ValueError("Unified analytical state policy version does not match the application release.")
    return payload


def _country_codes(settings: Settings) -> set[str]:
    payload = public_data_truth_countries(settings)
    return {str(item.get("code") or "").upper() for item in payload.get("countries") or []}


def _clean_token(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if TOKEN_RE.fullmatch(text) else default


def _clean_date(value: Any) -> str:
    text = str(value or "").strip()
    if not DATE_RE.fullmatch(text):
        return ""
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return ""
    return text


def _clean_categories(value: Any) -> list[str]:
    rows = value if isinstance(value, list) else str(value or "").split(",")
    cleaned: list[str] = []
    for item in rows:
        text = str(item or "").strip()
        if text and CATEGORY_RE.fullmatch(text) and text not in cleaned:
            cleaned.append(text)
    return cleaned[:12]


def _fingerprint(state: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(state), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


class UnifiedAnalyticalStateCenter:
    """Normalize portable analytical state without inventing data availability."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.policy = _policy()
        self.countries = _country_codes(settings)
        self.routes = dict(self.policy["routes"])

    def schema(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "unified-analytical-workspace-state",
            "default_route": self.policy["default_route"],
            "default_country": self.policy["default_country"],
            "default_compare": self.policy["default_compare"],
            "route_count": len(self.routes),
            "routes": self.routes,
            "shared_fields": list(self.policy["shared_fields"]),
            "handoff_targets": dict(self.policy["handoff_targets"]),
            "country_catalog_count": len(self.countries),
            "storage": {"browser": "session-and-local", "server": False, "account_required": False},
            "boundaries": list(self.policy["boundaries"]),
        }

    def normalize(self, raw: Mapping[str, Any] | None = None) -> dict[str, Any]:
        source = dict(raw or {})
        warnings: list[str] = []
        route = str(source.get("view") or source.get("route") or self.policy["default_route"]).strip().lower()
        if route not in self.routes:
            warnings.append(f"Unknown route '{route}' was replaced with {self.policy['default_route']}.")
            route = self.policy["default_route"]

        country = str(source.get("country") or self.policy["default_country"]).strip().upper()
        if country not in self.countries:
            warnings.append(f"Unknown country '{country}' was replaced with {self.policy['default_country']}.")
            country = self.policy["default_country"]

        compare = str(source.get("compare") or self.policy["default_compare"]).strip().upper()
        if compare not in self.countries or compare == country:
            candidates = [self.policy["default_compare"], "USA", "BRA", "IND", "GHA", "KEN"]
            compare = next((item for item in candidates if item in self.countries and item != country), next(code for code in sorted(self.countries) if code != country))
            warnings.append("Comparison country was invalid or matched the primary country and was replaced with a distinct supported country.")

        days_raw = source.get("eventDays", source.get("days", 30))
        try:
            event_days = max(1, min(365, int(days_raw)))
        except (TypeError, ValueError):
            event_days = 30
            warnings.append("Invalid event period was replaced with 30 days.")

        state = {
            "view": route,
            "country": country,
            "compare": compare,
            "indicator": _clean_token(source.get("indicator")),
            "imageryLayer": _clean_token(source.get("imageryLayer"), "true-color"),
            "imageryDate": _clean_date(source.get("imageryDate")),
            "area_id": _clean_token(source.get("area_id")),
            "dataset_id": _clean_token(source.get("dataset_id")),
            "layer_id": _clean_token(source.get("layer_id"), "true-color"),
            "date_a": _clean_date(source.get("date_a")),
            "date_b": _clean_date(source.get("date_b")),
            "eventDays": event_days,
            "mapCategories": _clean_categories(source.get("mapCategories")),
        }
        if state["date_a"] and state["date_b"] and state["date_a"] > state["date_b"]:
            state["date_a"], state["date_b"] = state["date_b"], state["date_a"]
            warnings.append("Earth observation dates were reordered chronologically.")
        applicable = set(self.routes[route]["fields"])
        retained = {key: value for key, value in state.items() if key == "view" or key in applicable or key in {"country", "compare"}}
        return {
            "ok": True,
            "version": APP_VERSION,
            "release_id": RELEASE_ID,
            "schema": SCHEMA_VERSION,
            "contract": "normalized-cross-view-state",
            "state": state,
            "route_state": retained,
            "workflow": self.routes[route],
            "warnings": warnings,
            "fingerprint": _fingerprint(state),
            "truth": {
                "country": f"/public/data-truth/country/{country}",
                "country_records": f"/public/record-truth/country/{country}",
                "control_plane": f"/public/data-truth/control-plane/workspaces?country={country}",
            },
            "boundaries": list(self.policy["boundaries"]),
        }

    @staticmethod
    def _query_value(value: Any) -> str | None:
        if value in (None, "", [], {}):
            return None
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value)

    def deep_link(self, raw: Mapping[str, Any] | None = None, target: str | None = None) -> dict[str, Any]:
        normalized = self.normalize(raw)
        state = dict(normalized["state"])
        if target:
            route = str(self.policy["handoff_targets"].get(str(target).lower()) or "")
            if not route:
                raise KeyError(target)
            state["view"] = route
            normalized = self.normalize(state)
            state = dict(normalized["state"])
        route = state["view"]
        fields = ["view", *self.routes[route]["fields"]]
        ordered: list[tuple[str, str]] = []
        for key in fields:
            value = self._query_value(state.get(key))
            if value is not None:
                ordered.append((key, value))
        query = urlencode(ordered)
        path = f"/app/?{query}"
        return {
            **normalized,
            "contract": "portable-analytical-deep-link",
            "target": route,
            "path": path,
            "query": query,
            "portable": True,
            "snapshot": False,
        }

    def handoff(self, target: str, raw: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = self.deep_link(raw, target=target)
        route = payload["target"]
        payload["contract"] = "cross-view-analytical-handoff"
        payload["destination"] = self.routes[route]
        payload["preserved_fields"] = [key for key in self.routes[route]["fields"] if payload["state"].get(key) not in (None, "", [])]
        return payload


def public_unified_analytical_state(settings: Settings) -> dict[str, Any]:
    return UnifiedAnalyticalStateCenter(settings).schema()


def public_normalize_analytical_state(settings: Settings, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return UnifiedAnalyticalStateCenter(settings).normalize(state)


def public_analytical_deep_link(settings: Settings, state: Mapping[str, Any] | None = None, target: str | None = None) -> dict[str, Any]:
    return UnifiedAnalyticalStateCenter(settings).deep_link(state, target=target)


def public_analytical_handoff(settings: Settings, target: str, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return UnifiedAnalyticalStateCenter(settings).handoff(target, state)
