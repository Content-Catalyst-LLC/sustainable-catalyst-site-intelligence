from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.country_identity_v43523 import country_identity_registry
from app.country_navigation_integrity_v43524 import readiness
from app.release_health_v43524 import deployment_verification
from app import live_country_intelligence as live


def _hostile_external_catalog():
    canonical = country_identity_registry()
    return {
        "ISR": {
            "code": "ISR", "iso2": "PS", "name": "Palestine",
            "latitude": canonical["PSE"]["latitude"], "longitude": canonical["PSE"]["longitude"],
            "income_level": "external-test", "source": "hostile-external-test",
        },
        "PSE": {
            "code": "PSE", "iso2": "IL", "name": "Israel",
            "latitude": canonical["ISR"]["latitude"], "longitude": canonical["ISR"]["longitude"],
            "income_level": "external-test", "source": "hostile-external-test",
        },
    }


def _reset_catalog():
    live._COUNTRY_CATALOG_CACHE = None
    live._COUNTRY_CATALOG_FETCHED_AT = None
    live._COUNTRY_CATALOG_STATE = "uninitialized"
    live._COUNTRY_CATALOG_TIMING_MS = 0.0


def test_external_catalog_cannot_swap_palestine_and_israel_identity():
    canonical = country_identity_registry()
    merged = live._merge_country_catalogs(canonical, _hostile_external_catalog())
    assert merged["PSE"]["name"] == "Palestine"
    assert merged["PSE"]["iso2"] == "PS"
    assert merged["PSE"]["latitude"] == canonical["PSE"]["latitude"]
    assert merged["PSE"]["longitude"] == canonical["PSE"]["longitude"]
    assert merged["ISR"]["name"] == "Israel"
    assert merged["ISR"]["iso2"] == "IL"
    assert merged["ISR"]["latitude"] == canonical["ISR"]["latitude"]
    assert merged["ISR"]["longitude"] == canonical["ISR"]["longitude"]
    assert merged["PSE"]["income_level"] == "external-test"
    assert merged["PSE"]["metadata_source"] == "hostile-external-test"


def test_country_catalog_keeps_canonical_identity_under_hostile_live_metadata(monkeypatch):
    _reset_catalog()
    monkeypatch.setattr(live, "_catalog_from_world_bank", _hostile_external_catalog)
    monkeypatch.setattr(live.country_cache, "set", lambda *args, **kwargs: "2026-08-12T00:00:00Z")
    payload = live.country_catalog(force_refresh=True)
    rows = {row["code"]: row for row in payload["countries"]}
    assert rows["PSE"]["name"] == "Palestine" and rows["PSE"]["iso2"] == "PS"
    assert rows["ISR"]["name"] == "Israel" and rows["ISR"]["iso2"] == "IL"
    assert rows["PSE"]["latitude"] != rows["ISR"]["latitude"]
    assert rows["PSE"]["longitude"] != rows["ISR"]["longitude"]


def test_navigation_readiness_proves_palestine_override_resistance_network_free():
    payload = readiness()
    assert payload["ok"] is True
    assert payload["network_calls_performed"] is False
    assert payload["upstream_health_release_blocking"] is False
    assert payload["checks"]["palestine_identity_survives_external_override"] is True
    assert payload["checks"]["israel_identity_survives_external_override"] is True
    assert payload["checks"]["palestine_and_israel_remain_distinct"] is True


def test_deployment_gate_requires_country_navigation_integrity():
    payload = deployment_verification(Settings(_env_file=None))
    assert payload["ok"] is True
    assert "/public/country-navigation-integrity/readiness" in payload["required_routes"]
    assert len(payload["required_routes"]) == 18
    assert payload["checks"]["palestine_external_override_blocked"] is True
    assert payload["checks"]["country_navigation_network_free"] is True
    client = TestClient(app)
    response = client.get("/public/country-navigation-integrity/readiness")
    assert response.status_code == 200
    assert response.json()["checks"]["palestine_identity_survives_external_override"] is True


def test_overview_selector_path_uses_canonical_focus_and_blocks_cross_identity_response():
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    map_js = (root / "backend/public_app/assets/cartographic-workspace-v3230.js").read_text(encoding="utf-8")
    assert "focus immediately from the first-party canonical registry" in app_js
    assert "country_identity_mismatch:${normalized}:${overviewCode" in app_js
    assert "latitude:canonical.latitude??item.latitude" in app_js
    assert "longitude:canonical.longitude??item.longitude" in app_js
    assert "latitude:canonical.latitude??item.latitude" in map_js
    assert "longitude:canonical.longitude??item.longitude" in map_js
    assert "merged.set(item.code,{...item,...canonical" in map_js


def test_runtime_release_is_v43524():
    root = Path(__file__).resolve().parents[2]
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    plugin = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-scsi-release="4.39.1"' in index
    assert 'const APP_VERSION="4.39.1"' in app_js
    assert "Version: 4.39.1" in plugin
    assert "site-intelligence-v4.39.1" in plugin
