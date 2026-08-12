from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.country_identity_v43523 import country_identity_registry, canonical_country, readiness
from app.data_truth_v32371 import public_data_truth_countries
from app import live_country_intelligence as live


def _network_free_catalog(monkeypatch):
    monkeypatch.setattr(live, "_catalog_from_world_bank", lambda: {})
    monkeypatch.setattr(live.country_cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(live.country_cache, "set", lambda *args, **kwargs: "2026-08-12T00:00:00+00:00")
    live._COUNTRY_CATALOG_CACHE = None
    live._COUNTRY_CATALOG_FETCHED_AT = None
    live._COUNTRY_CATALOG_STATE = "uninitialized"
    live._live_indicator_bundle.cache_clear()


def test_canonical_registry_binds_israel_and_palestine_independently():
    rows = country_identity_registry()
    assert len(rows) >= 170
    assert rows["ISR"]["name"] == "Israel"
    assert rows["ISR"]["iso2"] == "IL"
    assert rows["PSE"]["name"] == "Palestine"
    assert rows["PSE"]["iso2"] == "PS"
    assert rows["ISR"]["code"] != rows["PSE"]["code"]
    assert readiness()["checks"]["israel_iso3_bound_to_israel"] is True
    assert readiness()["checks"]["palestine_iso3_bound_to_palestine"] is True


def test_alias_resolution_does_not_cross_israel_palestine_boundary():
    assert canonical_country("ISR")[0] == "ISR"
    assert canonical_country("IL")[0] == "ISR"
    assert canonical_country("Israel")[0] == "ISR"
    assert canonical_country("PSE")[0] == "PSE"
    assert canonical_country("PS")[0] == "PSE"
    assert canonical_country("Palestine")[0] == "PSE"
    assert canonical_country("State of Palestine")[0] == "PSE"


def test_country_catalog_keeps_israel_and_palestine_when_upstream_catalog_is_unavailable(monkeypatch):
    _network_free_catalog(monkeypatch)
    payload = live.country_catalog(force_refresh=True)
    rows = {item["code"]: item for item in payload["countries"]}
    assert payload["country_count"] >= 170
    assert rows["ISR"]["name"] == "Israel" and rows["ISR"]["iso2"] == "IL"
    assert rows["PSE"]["name"] == "Palestine" and rows["PSE"]["iso2"] == "PS"
    assert payload["data_state"] == "fallback-catalog"


def test_data_truth_catalog_uses_same_israel_palestine_identity_bindings():
    payload = public_data_truth_countries(Settings(_env_file=None))
    rows = {item["code"]: item for item in payload["countries"]}
    assert rows["ISR"]["name"] == "Israel" and rows["ISR"]["iso2"] == "IL"
    assert rows["PSE"]["name"] == "Palestine" and rows["PSE"]["iso2"] == "PS"
    assert rows["ISR"]["catalog_source"] == "bundled-canonical-country-identity-v43523"
    assert rows["PSE"]["catalog_source"] == "bundled-canonical-country-identity-v43523"


def test_country_overview_routes_remain_distinct_during_upstream_failure(monkeypatch):
    _network_free_catalog(monkeypatch)
    monkeypatch.setattr(live, "_indicator_series", lambda iso2, indicator_id: ([], {"state":"unavailable","retrieved_at":None,"stale":False,"timing_ms":0.0}))
    live._live_indicator_bundle.cache_clear()
    client = TestClient(app)
    israel = client.get("/public/country/ISR/overview")
    palestine = client.get("/public/country/PSE/overview")
    assert israel.status_code == 200
    assert palestine.status_code == 200
    assert israel.json()["country"]["code"] == "ISR"
    assert israel.json()["country"]["name"] == "Israel"
    assert israel.json()["country"]["iso2"] == "IL"
    assert palestine.json()["country"]["code"] == "PSE"
    assert palestine.json()["country"]["name"] == "Palestine"
    assert palestine.json()["country"]["iso2"] == "PS"


def test_country_search_returns_distinct_results_for_israel_and_palestine(monkeypatch):
    _network_free_catalog(monkeypatch)
    client = TestClient(app)
    israel = client.get("/public/countries/search", params={"q":"Israel"}).json()["countries"]
    palestine = client.get("/public/countries/search", params={"q":"Palestine"}).json()["countries"]
    assert any(item["code"] == "ISR" and item["name"] == "Israel" for item in israel)
    assert not any(item["code"] == "PSE" and item["name"] == "Palestine" for item in israel)
    assert any(item["code"] == "PSE" and item["name"] == "Palestine" for item in palestine)
    assert not any(item["code"] == "ISR" and item["name"] == "Israel" for item in palestine)
