from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import scientific_earth_systems_observatory as module
from app.config import get_settings
from app.main import app

client = TestClient(app)


def settings(**overrides):
    values = {
        "platform_core_enabled": True,
        "platform_core_url": "https://core.example.test",
        "platform_core_public_api_key": "test-public-key",
        "scientific_earth_systems_enabled": True,
        "scientific_earth_systems_timeout_seconds": 9,
        "scientific_earth_systems_cache_ttl_seconds": 120,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def science_record(**overrides):
    value = {
        "id": "science-1",
        "raw_record_id": "must-not-leak",
        "source_record_id": "C123",
        "source_id": "nasa-earthdata",
        "connector_id": "nasa.earthdata-cmr",
        "record_type": "earth_science_dataset",
        "discipline": "earth science",
        "title": "Global Surface Water Dataset",
        "summary": "Official dataset metadata fixture.",
        "dataset_id": "C123",
        "collection": "Earth observations",
        "mission": "Terra",
        "instrument": "MODIS",
        "target": "Earth",
        "doi": "10.1234/example",
        "access_url": "https://example.test/data?token=must-not-leak",
        "landing_page_url": "https://example.test/record?api_key=must-not-leak",
        "geometry": {"type": "Point", "coordinates": [12.0, 34.0]},
        "observation_start": "2025-01-01T00:00:00Z",
        "observation_end": "2025-01-02T00:00:00Z",
        "published_at": "2025-01-03T00:00:00Z",
        "identifiers": {"cmr": "C123", "secret": "must-not-leak"},
        "keywords": ["water", "satellite"],
        "variables": ["surface water"],
        "file_formats": ["NetCDF", "GeoTIFF"],
        "quality_status": "validated",
        "license_name": "CC BY 4.0",
        "attribution": "NASA",
        "content_hash": "a" * 64,
        "metadata": {"processing_level": "L3", "authorization": "must-not-leak"},
        "public": True,
    }
    value.update(overrides)
    return value


def envelope(items, total=None):
    return {"data": items, "meta": {"pagination": {"total": len(items) if total is None else total, "limit": 100, "offset": 0}}}


def fake_core(config, path, query=None, **kwargs):
    if path == "/api/v1/science/records":
        return envelope([science_record()])
    if path == "/api/v1/fabric/assets":
        return envelope([{
            "id": "asset-1", "scientific_record_id": "science-1", "source_id": "nasa-earthdata",
            "connector_id": "nasa.earthdata-cmr", "dataset_id": "C123", "title": "NetCDF data",
            "asset_role": "data", "media_type": "application/x-netcdf", "format": "netcdf",
            "href": "https://example.test/file.nc?token=must-not-leak", "storage_mode": "remote",
            "size_bytes": 1000, "checksum": None, "stac_roles": ["data"], "variables": ["water"],
            "spatial_extent": [], "temporal_extent": [], "license_name": "CC BY 4.0",
            "attribution": "NASA", "metadata": {"secret": "must-not-leak"},
        }])
    if path == "/api/v1/fabric/map-layers":
        return envelope([{
            "id": "layer-1", "source_id": "nasa-gibs", "connector_id": "nasa.gibs",
            "external_layer_id": "MODIS_Terra", "title": "MODIS true color", "description": "Daily imagery",
            "layer_type": "wmts", "endpoint_url": "https://example.test/wmts?api_key=must-not-leak",
            "tile_template": "", "style": {}, "bounds": [-180, -90, 180, 90], "min_zoom": 0,
            "max_zoom": 9, "time_enabled": True, "license_name": "NASA terms", "attribution": "NASA",
            "status": "active", "metadata": {},
        }])
    if path == "/api/v1/fabric/timeseries":
        return envelope([{
            "id": "series-1", "source_id": "usgs-water", "connector_id": "usgs.water",
            "metric": "streamflow", "title": "Streamflow", "description": "Observed streamflow",
            "dataset_id": "station-1", "domain": "hydrology", "unit": "ft3/s", "frequency": "hourly",
            "geography_code": "USA", "dimensions": {}, "license_name": "Public domain", "attribution": "USGS",
        }])
    if path.endswith("/points"):
        return envelope([
            {"id": "p2", "series_id": "series-1", "observed_at": "2025-01-02T00:00:00Z", "value_number": 12.0, "value_text": None, "quality_status": "validated", "freshness_status": "latest", "dimensions": {}},
            {"id": "p1", "series_id": "series-1", "observed_at": "2025-01-01T00:00:00Z", "value_number": 10.0, "value_text": None, "quality_status": "validated", "freshness_status": "latest", "dimensions": {}},
        ])
    if path == "/api/v1/stac/search":
        return {"type": "FeatureCollection", "features": [{
            "type": "Feature", "id": "stac-1", "collection": "C123",
            "geometry": {"type": "Point", "coordinates": [12.0, 34.0]}, "bbox": [12, 34, 12, 34],
            "properties": {"title": "STAC item", "source_id": "nasa-earthdata", "token": "must-not-leak"},
            "assets": {"data": {"href": "https://example.test/stac.tif?key=must-not-leak", "type": "image/tiff", "roles": ["data"]}},
        }], "numberMatched": 1, "numberReturned": 1}
    if path in {"/api/v1/fabric/capabilities", "/api/v1/stac"}:
        return {"ok": True}
    raise AssertionError(path)


def test_unconfigured_core_returns_explicit_empty_state():
    payload = module.build_science_overview(settings(platform_core_enabled=False, platform_core_url=""))
    assert payload["integration"]["state"] == "core-unconfigured"
    assert payload["counts"]["scientific_records"] == 0
    assert payload["capabilities"]["fabrication_fallback"] is False
    assert payload["integration"]["credential_exposed"] is False


def test_public_record_sanitizes_credentials_and_preserves_science_context(monkeypatch):
    monkeypatch.setattr(module, "_core_json", fake_core)
    payload = module.build_science_records(settings(), limit=25)
    item = payload["records"][0]
    assert item["record_type"] == "earth_science_dataset"
    assert item["family"] == "earth-systems"
    assert item["mission"] == "Terra"
    assert item["instrument"] == "MODIS"
    assert item["quality_label"] == "VALIDATED"
    assert "token" not in item["access_url"]
    assert "api_key" not in item["landing_page_url"]
    assert "authorization" not in item["metadata"]
    assert "raw_record_id" not in item
    assert "test-public-key" not in str(payload)


def test_assets_layers_stac_and_series_are_public_safe(monkeypatch):
    monkeypatch.setattr(module, "_core_json", fake_core)
    asset = module.build_science_assets(settings())["assets"][0]
    layer = module.build_science_layers(settings())["layers"][0]
    stac = module.build_science_stac(settings())["features"][0]
    series = module.build_science_series(settings())["series"][0]
    points = module.build_science_series_points(settings(), series_id="series-1")["points"]
    assert asset["format"] == "netcdf"
    assert "token" not in asset["href"]
    assert "api_key" not in layer["endpoint_url"]
    assert "token" not in stac["properties"]
    assert "key" not in stac["assets"]["data"]["href"]
    assert series["metric"] == "streamflow"
    assert [point["id"] for point in points] == ["p1", "p2"]


def test_invalid_stac_bbox_is_rejected():
    with pytest.raises(ValueError):
        module.build_science_stac(settings(), bbox="200,0,201,1")


def test_public_routes(monkeypatch):
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_ENABLED", "true")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_URL", "https://core.example.test")
    monkeypatch.setenv("SC_SI_PLATFORM_CORE_PUBLIC_API_KEY", "test-public-key")
    monkeypatch.setenv("SC_SI_SCIENTIFIC_EARTH_SYSTEMS_ENABLED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(module, "_core_json", fake_core)
    responses = [
        client.get("/public/scientific-earth-systems"),
        client.get("/public/scientific-earth-systems/records?limit=10"),
        client.get("/public/scientific-earth-systems/facets"),
        client.get("/public/scientific-earth-systems/assets"),
        client.get("/public/scientific-earth-systems/map-layers"),
        client.get("/public/scientific-earth-systems/stac"),
        client.get("/public/scientific-earth-systems/timeseries"),
        client.get("/public/scientific-earth-systems/timeseries/series-1/points"),
        client.get("/public/scientific-earth-systems/brief"),
        client.get("/public/scientific-earth-systems/diagnostics"),
    ]
    assert all(response.status_code == 200 for response in responses)
    assert responses[1].json()["records"][0]["mission"] == "Terra"
    assert responses[0].json()["capabilities"]["paid_provider_required"] is False


def test_public_interface_wordpress_and_release_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/science-v240.js").read_text()
    css = (root / "backend/public_app/assets/science-v240.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="science"' in html
    assert 'id="scienceStudio"' in html
    assert "SCScienceV240" in js
    assert ".science-studio" in css
    assert 'const APP_VERSION="2.5.0"' in app_js
    assert "Version: 2.5.0" in php
    assert "sc_scientific_earth_systems_observatory" in php
    assert "No silent scientific inference" in html
