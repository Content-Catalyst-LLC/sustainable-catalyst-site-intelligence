from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient
import pytest

from app import authoritative_connectors_v4353 as connectors
from app.authoritative_api_audit_v4353 import audit_overview, source_inventory
from app.config import Settings
from app.main import app
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[2]


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_and_connector_catalog_are_v4353():
    assert APP_VERSION == "4.35.13"
    data = connectors.connector_catalog(settings())
    assert data["version"] == "4.35.13"
    assert data["connector_count"] == 5
    assert data["live_connector_count"] == 4
    assert data["discovery_connector_count"] == 1
    assert {row["id"] for row in data["connectors"]} == {
        "usgs-water-ogc-v0",
        "noaa-coastwatch-erddap",
        "nasa-exoplanet-tap",
        "unhcr-refugee-statistics-v1",
        "nasa-cmr-search",
    }


def test_connector_readiness_is_deterministic_and_no_network(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    data = connectors.connector_readiness(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False
    assert all(data["checks"].values())


def test_usgs_water_builds_bounded_ogc_query_and_preserves_quality(monkeypatch):
    captured = {}
    payload = {
        "numberMatched": 2,
        "numberReturned": 2,
        "features": [
            {
                "id": "series-1",
                "geometry": {"type": "Point", "coordinates": [-87.62, 41.88]},
                "properties": {
                    "time_series_id": "USGS-1",
                    "monitoring_location_id": "USGS-05586300",
                    "parameter_code": "00060",
                    "time": "2026-08-10T12:00:00Z",
                    "value": "1250",
                    "unit_of_measure": "ft3/s",
                    "approval_status": "Provisional",
                    "qualifier": ["P"],
                    "last_modified": "2026-08-10T12:05:00Z",
                },
            },
            {
                "id": "series-2",
                "geometry": {"type": "Point", "coordinates": [-87.60, 41.90]},
                "properties": {
                    "time_series_id": "USGS-2",
                    "monitoring_location_id": "USGS-2",
                    "parameter_code": "00060",
                    "time": "2026-08-10T12:00:00Z",
                    "value": None,
                    "unit_of_measure": "ft3/s",
                    "approval_status": "Approved",
                    "qualifier": None,
                },
            },
        ],
    }

    def fake(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        return payload

    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.usgs_water_latest(settings(usgs_water_api_key="secret-test-key"), latitude=41.88, longitude=-87.63, parameter_code="00060")
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert parsed.netloc == "api.waterdata.usgs.gov"
    assert parsed.path.endswith("/collections/latest-continuous/items")
    assert "bbox" in params and params["f"] == ["json"]
    assert captured["headers"]["X-Api-Key"] == "secret-test-key"
    assert data["observations"][0]["approval_status"] == "Provisional"
    assert data["observations"][0]["numeric_value"] == 1250.0
    assert data["observations"][1]["value"] is None
    assert data["observations"][1]["numeric_value"] is None
    assert data["observations"][1]["missing"] is True


def test_usgs_water_api_key_is_optional_and_never_returned(monkeypatch):
    captured = {}
    def fake(url, **kwargs):
        captured["headers"] = kwargs.get("headers", {})
        return {"features": []}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.usgs_water_latest(settings(), latitude=0, longitude=0)
    assert "X-Api-Key" not in captured["headers"]
    assert "api_key" not in str(data).lower()


def test_erddap_search_normalizes_table_response(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda url, **kwargs: {
        "table": {
            "columnNames": ["Dataset ID", "Title", "Institution"],
            "columnTypes": ["String", "String", "String"],
            "columnUnits": [None, None, None],
            "rows": [["dataset_a", "Sea Surface Temperature", "NOAA"], ["dataset_b", None, "NOAA"]],
        }
    })
    data = connectors.noaa_erddap_search(settings(), query="sea surface temperature", limit=10)
    assert data["result_count"] == 2
    assert data["datasets"][0]["Dataset ID"] == "dataset_a"
    assert data["datasets"][1]["Title"] is None


def test_erddap_data_requires_bounded_constraint_and_preserves_null(monkeypatch):
    with pytest.raises(ValueError, match="constraint"):
        connectors.noaa_erddap_tabledap(settings(), dataset_id="dataset_a", variables=["time", "sst"], constraints=[])
    captured = {}
    def fake(url, **kwargs):
        captured["url"] = url
        return {"table": {"columnNames": ["time", "sst"], "rows": [["2026-08-10T00:00:00Z", None]]}}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.noaa_erddap_tabledap(
        settings(), dataset_id="dataset_a", variables=["time", "sst"], constraints=["time>=2026-08-10T00:00:00Z"]
    )
    assert "/tabledap/dataset_a.json?" in captured["url"]
    assert data["records"][0]["sst"] is None


def test_erddap_rejects_arbitrary_hosts_and_unsafe_identifiers(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("invalid request must not call upstream"))
    with pytest.raises(ValueError):
        connectors.noaa_erddap_tabledap(settings(), dataset_id="https://evil.example/x", variables=["time"], constraints=["time>=2026-01-01T00:00:00Z"])
    with pytest.raises(ValueError):
        connectors.noaa_erddap_tabledap(settings(), dataset_id="safe", variables=["time;drop"], constraints=["time>=2026-01-01T00:00:00Z"])


def test_exoplanet_tap_query_is_fixed_to_pscomppars_and_normalizes_units(monkeypatch):
    captured = {}
    def fake(url, **kwargs):
        captured["url"] = url
        return [{"pl_name":"TRAPPIST-1 e","hostname":"TRAPPIST-1","discoverymethod":"Transit","disc_year":2017,"pl_orbper":6.1,"pl_rade":0.92,"pl_bmasse":0.69,"pl_eqt":250,"sy_dist":12.4}]
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.nasa_exoplanet_planets(settings(), target="TRAPPIST-1", limit=25)
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    adql = params["query"][0]
    assert parsed.netloc == "exoplanetarchive.ipac.caltech.edu"
    assert "from pscomppars" in adql
    assert "TRAPPIST-1".lower() in adql.lower()
    assert params["format"] == ["json"]
    assert data["records"][0]["equilibrium_temperature_k"] == 250
    assert data["units"]["equilibrium_temperature_k"] == "K"
    assert "not a measured surface temperature" in data["boundary"]


def test_exoplanet_target_quotes_are_escaped_in_adql(monkeypatch):
    captured = {}
    monkeypatch.setattr(connectors, "_request_json", lambda url, **kwargs: captured.setdefault("url", url) and [])
    connectors.nasa_exoplanet_planets(settings(), target="O'Brien", limit=5)
    adql = parse_qs(urlparse(captured["url"]).query)["query"][0]
    assert "o''brien" in adql.lower()


def test_unhcr_population_uses_iso3_filters_and_preserves_raw_records(monkeypatch):
    captured = {}
    record = {"year": 2025, "coo_name": "Palestine", "coo_iso": "PSE", "refugees": 123}
    def fake(url, **kwargs):
        captured["url"] = url
        return {"items": [record]}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.unhcr_population(settings(), year=2025, origin="PSE", asylum="JOR", limit=20)
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert parsed.netloc == "api.unhcr.org"
    assert parsed.path.endswith("/population/v1/population/")
    assert params["coo"] == ["PSE"] and params["coa"] == ["JOR"] and params["cf_type"] == ["ISO"]
    assert data["records"] == [record]
    assert "not a real-time" not in data["boundary"].lower() or "periodic" in data["boundary"].lower()


def test_unhcr_rejects_non_iso3_country_filter_without_network(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("invalid ISO must not call upstream"))
    with pytest.raises(ValueError, match="ISO3"):
        connectors.unhcr_population(settings(), origin="PS")


def test_nasa_cmr_is_discovery_and_sends_client_id(monkeypatch):
    captured = {}
    def fake(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        return {"feed":{"entry":[{"id":"C1","title":"SMAP Soil Moisture"}]}}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.nasa_cmr_collections(settings(), query="soil moisture", limit=10)
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert parsed.netloc == "cmr.earthdata.nasa.gov"
    assert parsed.path.endswith("/search/collections.json")
    assert params["keyword"] == ["soil moisture"]
    assert captured["headers"]["Client-Id"] == "sustainable-catalyst-site-intelligence"
    assert data["mode"] == "DISCOVERY"
    assert "not observation values" in data["boundary"]


def test_audit_promotes_new_hosts_but_keeps_cmr_discovery():
    rows = source_inventory(settings())
    by_host = {}
    for row in rows:
        by_host.setdefault(row.get("host"), set()).add(row["access_class"])
    assert by_host["api.waterdata.usgs.gov"] == {"LIVE"}
    assert by_host["coastwatch.noaa.gov"] == {"LIVE"}
    assert by_host["exoplanetarchive.ipac.caltech.edu"] == {"LIVE"}
    assert by_host["api.unhcr.org"] == {"LIVE"}
    assert by_host["cmr.earthdata.nasa.gov"] == {"DISCOVERY"}
    overview = audit_overview(settings())
    completed = {row["id"] for row in overview["completed_connector_targets"]}
    assert len(completed) == 5
    assert overview["summary"]["registered_but_not_retrieved"] < 70


def test_humanitarian_registry_is_reliefweb_v2_and_unhcr_live_connector():
    source = (ROOT / "backend/app/humanitarian_intelligence.py").read_text(encoding="utf-8")
    assert "https://api.reliefweb.int/v2" in source
    assert "https://api.reliefweb.int/v1" not in source
    assert "live_periodic_statistics_connector" in source


def test_public_connector_catalog_and_readiness_routes_are_network_free():
    client = TestClient(app)
    catalog = client.get("/public/authoritative-connectors")
    readiness = client.get("/public/authoritative-connectors/readiness")
    assert catalog.status_code == 200 and catalog.json()["connector_count"] >= 5
    assert readiness.status_code == 200 and readiness.json()["ok"] is True


def test_public_live_routes_use_connector_functions_without_real_network(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main, "build_usgs_water_latest", lambda settings, **kwargs: {"ok":True,"connector_id":"usgs-water-ogc-v0","query":kwargs})
    monkeypatch.setattr(main, "build_noaa_erddap_search", lambda settings, **kwargs: {"ok":True,"connector_id":"noaa-coastwatch-erddap","query":kwargs})
    monkeypatch.setattr(main, "build_nasa_exoplanet_planets", lambda settings, **kwargs: {"ok":True,"connector_id":"nasa-exoplanet-tap","query":kwargs})
    monkeypatch.setattr(main, "build_unhcr_population", lambda settings, **kwargs: {"ok":True,"connector_id":"unhcr-refugee-statistics-v1","query":kwargs})
    monkeypatch.setattr(main, "build_nasa_cmr_collections", lambda settings, **kwargs: {"ok":True,"connector_id":"nasa-cmr-search","query":kwargs})
    client=TestClient(app)
    assert client.get("/public/hydrology/live/usgs-water", params={"latitude":41.88,"longitude":-87.63}).status_code == 200
    assert client.get("/public/ocean-intelligence/erddap/search", params={"query":"sst"}).status_code == 200
    assert client.get("/public/exoplanet-habitability/live", params={"target":"TRAPPIST-1"}).status_code == 200
    assert client.get("/public/humanitarian-intelligence/displacement/live", params={"year":2025,"origin":"PSE"}).status_code == 200
    assert client.get("/public/science-discovery/nasa-cmr", params={"query":"soil moisture"}).status_code == 200
