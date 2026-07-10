from app.humanitarian_intelligence import overview, source_registry, crisis_map, displacement_context, methodology

def test_humanitarian_registry():
    data=source_registry()
    assert data["version_scope"] == "v1.10.0"
    assert data["counts"]["sources"] == 5
    assert {x["source_id"] for x in data["connectors"]} == {"gdacs","reliefweb","usgs-earthquakes","nasa-eonet","unhcr-refugee-statistics"}

def test_humanitarian_overview_and_map():
    assert overview()["schema"] == "sc-humanitarian-intelligence/1.0"
    layers=crisis_map()["layers"]
    assert len(layers) == 5
    assert any(x["source_id"] == "usgs-earthquakes" for x in layers)

def test_displacement_and_methodology():
    assert "refugees" in displacement_context()["population_categories"]
    assert "normalized_event_schema" in methodology()
