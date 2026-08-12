from __future__ import annotations

from urllib.parse import parse_qs, urlparse
import pytest
from fastapi.testclient import TestClient

from app import authoritative_connectors_v4356 as connectors
from app.authoritative_api_audit_v4356 import audit_overview, audit_readiness, source_inventory
from app.config import Settings
from app.main import app
from app.version import APP_VERSION


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_catalog_expands_to_twenty_interfaces():
    assert APP_VERSION == "4.35.21"
    data = connectors.connector_catalog(settings())
    assert data["connector_count"] == 20
    assert data["live_connector_count"] == 16
    assert data["discovery_connector_count"] == 2
    assert data["auth_required_connector_count"] == 2
    assert data["expansion_vi_connector_count"] == 5


def test_connector_readiness_is_network_free(monkeypatch):
    monkeypatch.setattr(connectors.expansion_iii, "_request_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    monkeypatch.setattr(connectors.expansion_iii, "_post_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    monkeypatch.setattr(connectors.expansion_iii, "_request_csv", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    data = connectors.connector_readiness(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False


def test_pcbs_metadata_uses_bounded_pxweb_path(monkeypatch):
    captured = {}
    def fake(url, **kwargs):
        captured["url"] = url
        return {"title":"Electricity access","variables":[{"code":"AREA"}]}
    monkeypatch.setattr(connectors.expansion_iii, "_request_json", fake)
    data = connectors.pcbs_pxweb_metadata(settings(), table_path="myDb/START/07/T32/C070101/S32C07010101")
    assert captured["url"].endswith("/myDb/START/07/T32/C070101/S32C07010101")
    assert data["metadata"]["title"] == "Electricity access"
    with pytest.raises(ValueError):
        connectors.pcbs_pxweb_metadata(settings(), table_path="../../etc/passwd")


def test_pcbs_data_requires_explicit_bounded_selections_and_preserves_null(monkeypatch):
    captured = {}
    payload = {"version":"2.0","class":"dataset","value":[100.0, None],"status":None}
    def fake(url, body, **kwargs):
        captured["url"] = url
        captured["body"] = body
        return payload
    monkeypatch.setattr(connectors.expansion_iii, "_post_json", fake)
    data = connectors.pcbs_pxweb_data(
        settings(),
        table_path="myDb/START/07/T32/C070101/S32C07010101",
        selections=["AREA=PS", "TIME PERIOD=2024,2025"],
    )
    assert captured["body"]["response"]["format"] == "json-stat2"
    assert data["data"]["value"] == [100.0, None]
    assert data["requested_cell_upper_bound"] == 2
    with pytest.raises(ValueError, match="wildcard"):
        connectors.pcbs_pxweb_data(settings(), table_path="myDb/X", selections=["AREA=*"])


def test_statcan_wds_uses_official_latest_period_method(monkeypatch):
    captured = {}
    def fake(url, body, **kwargs):
        captured["url"] = url; captured["body"] = body
        return [{"status":"SUCCESS","object":{"vectorId":32164132,"vectorDataPoint":[{"value":12.3,"statusCode":7,"releaseTime":"2026-08-01T08:30"}]}}]
    monkeypatch.setattr(connectors.expansion_iii, "_post_json", fake)
    data = connectors.statcan_vectors(settings(), vector_ids=[32164132], latest_n=3)
    assert captured["url"].endswith("/getDataFromVectorsAndLatestNPeriods")
    assert captured["body"] == [{"vectorId":32164132,"latestN":3}]
    assert data["data"][0]["object"]["vectorDataPoint"][0]["statusCode"] == 7


def test_statcan_rejects_unbounded_vector_requests(monkeypatch):
    monkeypatch.setattr(connectors.expansion_iii, "_post_json", lambda *_a, **_k: pytest.fail("invalid query must not call upstream"))
    with pytest.raises(ValueError): connectors.statcan_vectors(settings(), vector_ids=[], latest_n=3)
    with pytest.raises(ValueError): connectors.statcan_vectors(settings(), vector_ids=list(range(1,12)), latest_n=3)
    with pytest.raises(ValueError): connectors.statcan_vectors(settings(), vector_ids=[1], latest_n=25)


def test_ons_observation_query_preserves_explicit_version_and_dimensions(monkeypatch):
    captured = {}
    def fake(url, **kwargs): captured["url"] = url; return {"observations":["123.4"],"dimensions":{}}
    monkeypatch.setattr(connectors.expansion_iii, "_request_json", fake)
    data = connectors.ons_observations(settings(), dataset_id="cpih01", edition="time-series", version=6, filters=["time=*","geography=K02000001","aggregate=cpih1dim1A0"])
    assert "/datasets/cpih01/editions/time-series/versions/6/observations?" in captured["url"]
    q=parse_qs(urlparse(captured["url"]).query)
    assert q["time"] == ["*"] and q["geography"] == ["K02000001"]
    assert data["dataset_version"] == 6


def test_ons_rejects_broad_wildcards(monkeypatch):
    monkeypatch.setattr(connectors.expansion_iii, "_request_json", lambda *_a, **_k: pytest.fail("invalid query must not call upstream"))
    with pytest.raises(ValueError): connectors.ons_observations(settings(), dataset_id="cpih01", edition="time-series", version=6, filters=["time=*"])
    with pytest.raises(ValueError): connectors.ons_observations(settings(), dataset_id="cpih01", edition="time-series", version=6, filters=["time=*","geography=*"])


def test_abs_sdmx_query_is_time_and_observation_bounded(monkeypatch):
    captured = {}
    def fake(url, **kwargs): captured["url"] = url; return [{"TIME_PERIOD":"2025-01","OBS_VALUE":"3.5","OBS_STATUS":"P"}]
    monkeypatch.setattr(connectors.expansion_iii, "_request_csv", fake)
    data = connectors.abs_sdmx_data(settings(), dataflow="ABS,CPI,1.0.0", data_key="1.10001.10.50.Q", start_period="2024-Q1", end_period="2026-Q4", limit=25)
    q=parse_qs(urlparse(captured["url"]).query)
    assert q["firstNObservations"] == ["25"] and q["format"] == ["csv"]
    assert data["records"][0]["OBS_STATUS"] == "P"
    with pytest.raises(ValueError, match="explicit"):
        connectors.abs_sdmx_data(settings(), dataflow="ABS,CPI,1.0.0", data_key="all", start_period="2024", end_period="2025")


def test_bls_public_v1_preserves_footnotes_and_bounds_years(monkeypatch):
    captured = {}
    payload={"status":"REQUEST_SUCCEEDED","Results":{"series":[{"seriesID":"CUUR0000SA0","data":[{"year":"2025","period":"M12","value":"321.0","footnotes":[{"code":"P","text":"Preliminary."}]}]}]}}
    def fake(url, body, **kwargs): captured["url"] = url; captured["body"] = body; return payload
    monkeypatch.setattr(connectors.expansion_iii, "_post_json", fake)
    data=connectors.bls_timeseries(settings(), series_ids=["CUUR0000SA0"], start_year=2020, end_year=2025)
    assert captured["url"].endswith("/timeseries/data/")
    assert captured["body"]["startyear"] == "2020"
    assert data["data"]["Results"]["series"][0]["data"][0]["footnotes"][0]["code"] == "P"
    with pytest.raises(ValueError, match="10 years"):
        connectors.bls_timeseries(settings(), series_ids=["CUUR0000SA0"], start_year=2010, end_year=2025)


def test_audit_adds_five_live_first_party_statistical_sources():
    rows = source_inventory(settings())
    ids={row["source_id"]: row for row in rows}
    expected={"pcbs-pxweb-sdgs","statistics-canada-wds","uk-ons-api","australian-bureau-statistics-sdmx","us-bls-public-data-api"}
    assert expected.issubset(ids)
    assert all(ids[source_id]["access_class"] == "LIVE" for source_id in expected)
    overview=audit_overview(settings())
    assert overview["summary"]["source_registrations"] == 184
    assert overview["summary"]["machine_readable_registrations"] == 101
    assert overview["summary"]["counts"]["LIVE"] == 46
    assert overview["summary"]["registered_but_not_retrieved"] == 45
    assert len(overview["completed_connector_targets"]) == 20


def test_audit_readiness_tracks_national_statistical_expansion_without_network():
    data=audit_readiness(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False


def test_public_routes_validate_before_upstream_network():
    client=TestClient(app)
    catalog=client.get("/public/authoritative-connectors")
    assert catalog.status_code == 200 and catalog.json()["connector_count"] == 50
    assert client.get("/public/authoritative-connectors/pcbs/pxweb/data",params={"table_path":"myDb/X"}).status_code == 400
    assert client.get("/public/authoritative-connectors/statcan/vectors").status_code == 400
    assert client.get("/public/authoritative-connectors/ons/observations",params={"dataset_id":"cpih01","edition":"time-series","version":6}).status_code == 400
    assert client.get("/public/authoritative-connectors/abs/sdmx",params={"dataflow":"ABS,CPI,1.0.0","data_key":"all","start_period":"2024","end_period":"2025"}).status_code == 400
    assert client.get("/public/authoritative-connectors/bls/timeseries").status_code == 400
