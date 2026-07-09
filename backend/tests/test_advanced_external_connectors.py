
from app.config import Settings
from app.connectors.advanced_external import AdvancedExternalDataHub


def settings():
    return Settings(external_live=False, demo_mode=True, registry_path="backend/data/site_registry.seed.json")


def test_advanced_health_fallbacks():
    hub = AdvancedExternalDataHub(settings())
    health = hub.health()
    ids = {item.connector_id for item in health}
    assert "noaa_weather_climate" in ids
    assert "gbif_biodiversity" in ids
    assert len(health) >= 6


def test_environmental_monitoring_dashboard_shape():
    data = AdvancedExternalDataHub(settings()).environmental_monitoring_dashboard()
    assert data["ok"] is True
    assert data["dashboard_id"] == "environmental_monitoring"
    assert data["indicators"]
    assert "Environmental Monitoring" in data["linked_article_maps"]


def test_urban_resilience_dashboard_shape():
    data = AdvancedExternalDataHub(settings()).urban_resilience_dashboard()
    assert data["ok"] is True
    assert data["dashboard_id"] == "urban_resilience"
    assert data["stability"]["fallback_sources"] >= 1


def test_biodiversity_and_energy_dashboards_shape():
    hub = AdvancedExternalDataHub(settings())
    bio = hub.biodiversity_land_use_dashboard()
    energy = hub.energy_systems_dashboard()
    assert bio["dashboard_id"] == "biodiversity_land_use"
    assert energy["dashboard_id"] == "energy_systems"
    assert bio["recommendations"]
    assert energy["recommendations"]
