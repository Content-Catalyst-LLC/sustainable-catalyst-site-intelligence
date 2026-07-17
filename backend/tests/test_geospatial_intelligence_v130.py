from app.geospatial_intelligence import overview, layer_manifest, live_events, heatmap, satellite_manifest, accessibility_table, diagnostics

def test_geospatial_overview_and_layers():
    data = overview()
    assert data["ok"] is True
    assert data["version"] == "3.0.0"
    manifest = layer_manifest()
    assert len(manifest["satellite_layers"]) >= 4
    assert any(layer["kind"] == "heat" for layer in manifest["vector_layers"])

def test_geojson_heat_and_satellite_contracts():
    events = live_events()
    assert events["type"] == "FeatureCollection"
    assert events["features"]
    assert heatmap()["points"]
    sat = satellite_manifest("2026-07-01")
    assert sat["selected_date"] == "2026-07-01"
    assert all("2026-07-01" in layer["resolved_tile_url"] for layer in sat["layers"])

def test_accessibility_and_diagnostics():
    table = accessibility_table()
    assert "title" in table["columns"]
    assert diagnostics()["checks"]
