from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
import pytest

from app import authoritative_connectors_v4354 as connectors
from app.authoritative_api_audit_v4354 import audit_overview, source_inventory
from app.config import Settings
from app.main import app
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[2]


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_and_combined_connector_catalog_are_v4354():
    assert APP_VERSION == "4.35.19"
    data = connectors.connector_catalog(settings())
    assert data["version"] == "4.35.19"
    assert data["connector_count"] == 10
    assert data["live_connector_count"] == 9
    assert data["discovery_connector_count"] == 1
    assert data["expansion_i_connector_count"] == 5
    assert data["expansion_ii_connector_count"] == 5
    assert {row["id"] for row in data["connectors"]}.issuperset({
        "noaa-coops-data-api", "noaa-ncei-access-data-v1", "obis-api-v3",
        "eurostat-statistics-api", "usda-nrcs-soil-data-access",
    })


def test_connector_readiness_remains_network_free(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    monkeypatch.setattr(connectors, "_post_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    data = connectors.connector_readiness(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False
    assert all(data["checks"].values())


def test_noaa_coops_builds_bounded_station_query_and_preserves_flags(monkeypatch):
    captured = {}
    def fake(url, **kwargs):
        captured["url"] = url
        return {
            "metadata": {"id": "8518750", "name": "The Battery"},
            "data": [
                {"t": "2026-08-10 12:00", "v": "0.412", "s": "0.013", "f": "0,0,0,0", "q": "p"},
                {"t": "2026-08-10 12:06", "v": None, "s": None, "f": "1,0,0,0", "q": "p"},
            ],
        }
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.noaa_coops_data(settings(), station="8518750", product="water_level", date_value="latest", datum="MSL")
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["station"] == ["8518750"]
    assert params["product"] == ["water_level"]
    assert params["date"] == ["latest"]
    assert params["datum"] == ["MSL"]
    assert data["records"][0]["q"] == "p"
    assert data["records"][1]["v"] is None


def test_noaa_coops_rejects_unsupported_product_without_network(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("invalid request must not call upstream"))
    with pytest.raises(ValueError, match="unsupported"):
        connectors.noaa_coops_data(settings(), station="8518750", product="delete_everything")
    with pytest.raises(ValueError):
        connectors.noaa_coops_data(settings(), station="9414290", begin_date="20260101", end_date="20260315")


def test_ncei_access_data_is_time_bounded_and_preserves_records(monkeypatch):
    captured = {}
    payload = [{"STATION": "USW00094846", "DATE": "2026-08-10", "PRCP": None, "TMAX": 28.3}]
    def fake(url, **kwargs):
        captured["url"] = url
        return payload
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.ncei_access_data(
        settings(), dataset="daily-summaries", start_date="2026-08-01", end_date="2026-08-10",
        stations=["USW00094846"], data_types=["PRCP", "TMAX"], units="metric",
    )
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["dataset"] == ["daily-summaries"]
    assert params["stations"] == ["USW00094846"]
    assert params["dataTypes"] == ["PRCP,TMAX"]
    assert data["records"][0]["PRCP"] is None


def test_ncei_rejects_unbounded_long_range(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("invalid request must not call upstream"))
    with pytest.raises(ValueError, match="366"):
        connectors.ncei_access_data(settings(), dataset="daily-summaries", start_date="2020-01-01", end_date="2026-01-01")


def test_obis_occurrence_filter_is_required_and_provenance_preserved(monkeypatch):
    with pytest.raises(ValueError, match="filter"):
        connectors.obis_occurrences(settings())
    captured = {}
    row = {"id": 1, "scientificName": "Delphinus delphis", "datasetID": "dataset-1", "flags": ["depth"]}
    def fake(url, **kwargs):
        captured["url"] = url
        return {"total": 123, "results": [row]}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.obis_occurrences(settings(), scientific_name="Delphinus delphis", size=25)
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["scientificname"] == ["Delphinus delphis"]
    assert params["size"] == ["25"]
    assert data["upstream_total"] == 123
    assert data["records"][0]["datasetID"] == "dataset-1"
    assert data["records"][0]["flags"] == ["depth"]


def test_eurostat_requires_dimension_filter_and_keeps_jsonstat(monkeypatch):
    with pytest.raises(ValueError, match="dimension filter"):
        connectors.eurostat_statistics(settings(), dataset_code="env_wasmun")
    captured = {}
    payload = {"version": "2.0", "id": ["freq", "unit", "wst_oper", "geo", "time"], "size": [1, 1, 1, 1, 1], "value": {"0": 512.0}, "status": {"0": "e"}}
    def fake(url, **kwargs):
        captured["url"] = url
        return payload
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.eurostat_statistics(settings(), dataset_code="env_wasmun", geo="DE", time="2024", filters=["unit=KG_HAB", "wst_oper=GEN"])
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["geo"] == ["DE"] and params["time"] == ["2024"]
    assert params["unit"] == ["KG_HAB"] and params["wst_oper"] == ["GEN"]
    assert data["value_count"] == 1
    assert data["data"]["status"]["0"] == "e"


def test_usda_soil_uses_fixed_bounded_query_not_user_sql(monkeypatch):
    captured = {}
    def fake(url, payload, **kwargs):
        captured["url"] = url
        captured["payload"] = payload
        return {"Table": [["mukey", "musym", "muname", "areasymbol"], ["123", "A", "Example soil", "IL031"]]}
    monkeypatch.setattr(connectors, "_post_json", fake)
    data = connectors.usda_soil_mapunits(settings(), area_symbol="IL031", limit=25)
    assert captured["url"].endswith("/Tabular/post.rest")
    assert "SELECT TOP 25" in captured["payload"]["query"]
    assert "IL031" in captured["payload"]["query"]
    assert captured["payload"]["format"] == "JSON+COLUMNNAME"
    assert data["records"][0]["muname"] == "Example soil"


def test_usda_soil_requires_exactly_one_safe_identifier(monkeypatch):
    monkeypatch.setattr(connectors, "_post_json", lambda *_a, **_k: pytest.fail("invalid request must not call upstream"))
    with pytest.raises(ValueError, match="exactly one"):
        connectors.usda_soil_mapunits(settings())
    with pytest.raises(ValueError, match="exactly one"):
        connectors.usda_soil_mapunits(settings(), mukey="123", area_symbol="IL031")
    with pytest.raises(ValueError):
        connectors.usda_soil_mapunits(settings(), area_symbol="CA001;DROP")


def test_audit_promotes_second_expansion_hosts_and_reduces_backlog():
    rows = source_inventory(settings())
    by_host = {}
    for row in rows:
        by_host.setdefault(row["host"], set()).add(row["access_class"])
    for host in ("api.tidesandcurrents.noaa.gov", "www.ncei.noaa.gov", "api.obis.org", "ec.europa.eu", "sdmdataaccess.sc.egov.usda.gov"):
        assert "LIVE" in by_host.get(host, set()), host
    overview = audit_overview(settings())
    assert len(overview["completed_connector_targets"]) == 10
    assert overview["summary"]["registered_but_not_retrieved"] < 56
    assert overview["summary"]["stale_implemented_connectors"] == 0


def test_public_routes_are_present_and_validation_errors_are_400(monkeypatch):
    client = TestClient(app)
    catalog = client.get("/public/authoritative-connectors")
    readiness = client.get("/public/authoritative-connectors/readiness")
    assert catalog.status_code == 200 and catalog.json()["connector_count"] >= 10
    assert readiness.status_code == 200 and readiness.json()["ok"] is True
    assert client.get("/public/authoritative-connectors/obis/occurrences").status_code == 400
    assert client.get("/public/authoritative-connectors/eurostat/statistics").status_code == 400
    assert client.get("/public/authoritative-connectors/usda-soils/mapunits").status_code == 400


def test_new_workspace_alias_routes_return_fixture_data(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda url, **kwargs: [] if "ncei.noaa.gov" in url else {"metadata": {}, "data": []})
    monkeypatch.setattr(connectors, "_post_json", lambda url, payload, **kwargs: {"Table": [["mukey"], ["123"]]})
    client = TestClient(app)
    assert client.get("/public/coastal-change/live/noaa-coops", params={"station": "8518750"}).status_code == 200
    assert client.get("/public/climate/live/noaa-ncei", params={"dataset": "daily-summaries", "start_date": "2026-08-01", "end_date": "2026-08-02"}).status_code == 200
    # OBIS route needs a filter and fake response shape is accepted.
    assert client.get("/public/biodiversity/live/obis", params={"scientific_name": "Mollusca"}).status_code == 200
    assert client.get("/public/soils-land/live/usda-nrcs", params={"mukey": "123"}).status_code == 200
