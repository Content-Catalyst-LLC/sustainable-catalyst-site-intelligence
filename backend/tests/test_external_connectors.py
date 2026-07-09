from app.config import Settings
from app.connectors.external_data import ExternalDataHub


def test_external_registry_loads():
    settings = Settings(external_live=False)
    hub = ExternalDataHub(settings)
    ids = {item.connector_id for item in hub.connectors()}
    assert {"nasa_power", "nasa_gibs", "climate_trace"}.issubset(ids)


def test_external_health_fallback_shape():
    settings = Settings(external_live=False)
    hub = ExternalDataHub(settings)
    health = hub.health()
    assert len(health) == 3
    assert all(item.status == "fallback" for item in health)


def test_climate_energy_dashboard_shape():
    settings = Settings(external_live=False)
    hub = ExternalDataHub(settings)
    data = hub.climate_energy_dashboard()
    assert data["ok"] is True
    assert data["source"] == "sample-fallback"
    assert data["indicators"]
    assert data["earth_observation_layers"]
    assert data["emissions_summary"]["top_sectors"]


def test_external_cache_records_sample_disabled_status():
    settings = Settings(external_live=False, external_cache_enabled=True)
    hub = ExternalDataHub(settings)
    data = hub.nasa_power_timeseries()
    assert data["cache"]["status"] == "disabled"


def test_climate_energy_dashboard_includes_stability_and_cache_summary():
    settings = Settings(external_live=False)
    hub = ExternalDataHub(settings)
    data = hub.climate_energy_dashboard()
    assert "stability" in data
    assert "cache_summary" in data
    assert data["stability"]["public_status"] == "internal_only"
