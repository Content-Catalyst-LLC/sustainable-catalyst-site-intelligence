from __future__ import annotations

from urllib.parse import parse_qs, urlparse
from fastapi.testclient import TestClient
import pytest

from app import authoritative_connectors_v4355 as connectors
from app.authoritative_api_audit_v4355 import audit_overview, source_inventory
from app.config import Settings
from app.main import app
from app.version import APP_VERSION


def settings(**updates):
    return Settings(_env_file=None, **updates)


def test_release_catalog_expands_to_fifteen_interfaces():
    assert APP_VERSION == "4.39.0"
    data = connectors.connector_catalog(settings())
    assert data["connector_count"] == 15
    assert data["live_connector_count"] == 11
    assert data["discovery_connector_count"] == 2
    assert data["auth_required_connector_count"] == 2
    assert data["configured_auth_required_connector_count"] == 0
    assert data["expansion_iii_connector_count"] == 5


def test_readiness_is_network_free(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    monkeypatch.setattr(connectors, "_request_csv", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    monkeypatch.setattr(connectors, "_post_json", lambda *_a, **_k: pytest.fail("readiness must not call upstream"))
    data = connectors.connector_readiness(settings())
    assert data["ok"] is True
    assert data["network_calls_performed"] is False


def test_nwi_uses_bounded_arcgis_point_query_and_preserves_geojson(monkeypatch):
    captured = {}
    payload = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"ATTRIBUTE":"PFO1A","WETLAND_TYPE":"Freshwater Forested/Shrub Wetland","ACRES":2.5},"geometry":None}]}
    def fake(url, **kwargs):
        captured["url"] = url
        return payload
    monkeypatch.setattr(connectors, "_request_json", fake)
    data = connectors.usfws_nwi_wetlands(settings(), latitude=41.88, longitude=-87.63, limit=25)
    q=parse_qs(urlparse(captured["url"]).query)
    assert q["geometryType"] == ["esriGeometryPoint"]
    assert q["resultRecordCount"] == ["25"]
    assert q["f"] == ["geojson"]
    assert data["record_count"] == 1
    assert data["data"]["features"][0]["properties"]["ATTRIBUTE"] == "PFO1A"


def test_nwi_rejects_unbounded_or_oversize_query(monkeypatch):
    monkeypatch.setattr(connectors, "_request_json", lambda *_a, **_k: pytest.fail("invalid query must not call upstream"))
    with pytest.raises(ValueError): connectors.usfws_nwi_wetlands(settings())
    with pytest.raises(ValueError): connectors.usfws_nwi_wetlands(settings(), latitude=41.0)
    with pytest.raises(ValueError, match="too large"): connectors.usfws_nwi_wetlands(settings(), bbox="-100,20,-80,40")


def test_echo_requires_facility_filter_and_preserves_raw_regulatory_payload(monkeypatch):
    with pytest.raises(ValueError, match="filter"):
        connectors.epa_echo_facilities(settings())
    captured={}
    payload={"Results":{"Facilities":[{"RegistryID":"110000000001","FacName":"Example"}]}}
    def fake(url, **kwargs): captured["url"]=url; return payload
    monkeypatch.setattr(connectors, "_request_json", fake)
    data=connectors.epa_echo_facilities(settings(), media="cwa", state="IL", limit=50)
    assert "/cwa_rest_services.get_facilities?" in captured["url"]
    q=parse_qs(urlparse(captured["url"]).query)
    assert q["p_st"] == ["IL"]
    assert data["data"]["Results"]["Facilities"][0]["RegistryID"] == "110000000001"


def test_firms_is_configuration_gated_then_preserves_csv_rows(monkeypatch):
    with pytest.raises(PermissionError, match="MAP_KEY"):
        connectors.nasa_firms_area(settings(), bbox="-90,40,-89,41")
    captured={}
    def fake(url, **kwargs): captured["url"]=url; return [{"latitude":"40.5","longitude":"-89.5","confidence":"n","frp":"2.24"}]
    monkeypatch.setattr(connectors, "_request_csv", fake)
    data=connectors.nasa_firms_area(settings(nasa_firms_map_key="ABCDEFGH12345678"), bbox="-90,40,-89,41", day_range=2)
    assert "/VIIRS_NOAA20_NRT/-90,40,-89,41/2" in captured["url"]
    assert data["records"][0]["confidence"] == "n"


def test_firms_rejects_large_bbox_and_bad_day_range_without_network(monkeypatch):
    monkeypatch.setattr(connectors, "_request_csv", lambda *_a, **_k: pytest.fail("invalid query must not call upstream"))
    s=settings(nasa_firms_map_key="ABCDEFGH12345678")
    with pytest.raises(ValueError, match="too large"): connectors.nasa_firms_area(s, bbox="-150,10,-50,70")
    with pytest.raises(ValueError, match="between 1 and 5"): connectors.nasa_firms_area(s, bbox="-90,40,-89,41", day_range=6)


def test_nass_is_configuration_gated_and_query_filters_are_allowlisted(monkeypatch):
    with pytest.raises(PermissionError, match="NASS"):
        connectors.usda_nass_quickstats(settings(), filters=["commodity_desc=CORN","year=2025"])
    captured={"urls":[]}
    def fake(url, **kwargs):
        captured["urls"].append(url)
        return {"count":"1"} if "/get_counts/" in url else {"data":[{"commodity_desc":"CORN","year":"2025","Value":"14,000"}]}
    monkeypatch.setattr(connectors, "_request_json", fake)
    data=connectors.usda_nass_quickstats(settings(usda_nass_api_key="ABCDEFGH12345678"), filters=["commodity_desc=CORN","year=2025","state_alpha=IL"], limit=20)
    assert len(captured["urls"]) == 2 and "/get_counts/" in captured["urls"][0] and "/api_GET/" in captured["urls"][1]
    q=parse_qs(urlparse(captured["urls"][1]).query)
    assert q["commodity_desc"] == ["CORN"] and q["year"] == ["2025"]
    assert q["key"] == ["ABCDEFGH12345678"]
    assert data["record_count"] == 1 and data["upstream_count"] == 1
    with pytest.raises(ValueError, match="unsupported"):
        connectors.usda_nass_quickstats(settings(usda_nass_api_key="ABCDEFGH12345678"), filters=["sql=DROP"])
    monkeypatch.setattr(connectors, "_request_json", lambda url, **kwargs: {"count":"501"})
    with pytest.raises(ValueError, match="narrow filters"):
        connectors.usda_nass_quickstats(settings(usda_nass_api_key="ABCDEFGH12345678"), filters=["commodity_desc=CORN","year=2025"], limit=500)


def test_cmr_graphql_is_bounded_discovery_and_preserves_metadata(monkeypatch):
    captured={}
    payload={"data":{"collections":{"count":7,"cursor":"abc","items":[{"conceptId":"C1-TEST","shortName":"SENTINEL-1A_SLC","provider":"ASF"}]}}}
    def fake(url,payload,**kwargs): captured["url"]=url; captured["payload"]=payload; return globals()["payload"] if False else {"data":{"collections":{"count":7,"cursor":"abc","items":[{"conceptId":"C1-TEST","shortName":"SENTINEL-1A_SLC","provider":"ASF"}]}}}
    monkeypatch.setattr(connectors, "_post_json", fake)
    data=connectors.nasa_cmr_graphql_collections(settings(), short_name="SENTINEL-1A_SLC", limit=10)
    assert captured["url"] == "https://graphql.earthdata.nasa.gov/api"
    assert captured["payload"]["variables"]["params"]["limit"] == 10
    assert data["mode"] == "DISCOVERY"
    assert data["collections"][0]["conceptId"] == "C1-TEST"
    with pytest.raises(ValueError): connectors.nasa_cmr_graphql_collections(settings())


def test_audit_promotes_public_hosts_and_gates_firms_nass():
    rows=source_inventory(settings())
    by_host={}
    for row in rows: by_host.setdefault(row["host"], set()).add(row["access_class"])
    assert "LIVE" in by_host.get("fwspublicservices.wim.usgs.gov",set())
    assert "LIVE" in by_host.get("echodata.epa.gov",set())
    assert "AUTH_REQUIRED" in by_host.get("firms.modaps.eosdis.nasa.gov",set())
    assert "AUTH_REQUIRED" in by_host.get("quickstats.nass.usda.gov",set())
    overview=audit_overview(settings())
    assert len(overview["completed_connector_targets"]) == 15
    assert overview["summary"]["registered_but_not_retrieved"] < 50


def test_configured_credentials_promote_firms_and_nass_inventory_to_live():
    rows=source_inventory(settings(nasa_firms_map_key="ABCDEFGH12345678", usda_nass_api_key="ABCDEFGH12345678"))
    by_host={}
    for row in rows: by_host.setdefault(row["host"], set()).add(row["access_class"])
    assert "LIVE" in by_host.get("firms.modaps.eosdis.nasa.gov",set())
    assert "LIVE" in by_host.get("quickstats.nass.usda.gov",set())


def test_public_routes_validate_and_auth_gates_without_upstream_calls(monkeypatch):
    client=TestClient(app)
    catalog=client.get("/public/authoritative-connectors")
    assert catalog.status_code == 200 and catalog.json()["connector_count"] == 50
    assert client.get("/public/authoritative-connectors/usfws-nwi/wetlands").status_code == 400
    assert client.get("/public/authoritative-connectors/epa-echo/facilities").status_code == 400
    assert client.get("/public/authoritative-connectors/nasa-firms/area", params={"bbox":"-90,40,-89,41"}).status_code == 503
    assert client.get("/public/authoritative-connectors/usda-nass/quick-stats", params={"filter":"year=2025"}).status_code == 503
    assert client.get("/public/authoritative-connectors/nasa-cmr/graphql/collections").status_code == 400
