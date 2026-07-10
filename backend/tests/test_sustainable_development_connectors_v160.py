from app.config import Settings
from app.sustainable_development_connectors import source_registry, source_families, planetary_boundary_registry, connector_health, methodology

def test_registry_has_flagship_sources():
    data=source_registry(Settings())
    ids={x["source_id"] for x in data["connectors"]}
    assert {"nasa-eonet","nasa-power","un-sdg","world-bank-indicators","world-bank-pip","unesco-uis","faostat","un-water-sdg6","oecd-sdmx"}.issubset(ids)
    assert data["observation_schema"]["schema"] == "sc-sustainable-development-observation/1.0"

def test_planetary_boundaries_complete():
    data=planetary_boundary_registry()
    assert data["counts"]["boundaries"] == 9
    assert all(item["source_mappings"] for item in data["boundaries"])

def test_health_is_network_safe_by_default():
    data=connector_health(Settings(), live=False)
    assert data["public_status"] == "registry_only"
    assert all(item["status"] == "configured" for item in data["connectors"])

def test_families_and_methodology():
    assert source_families()["families"]
    assert methodology()["observation_schema"]["required"]
