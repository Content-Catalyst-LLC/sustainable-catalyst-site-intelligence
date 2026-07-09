from app.main import app
from fastapi.testclient import TestClient


def test_public_climate_energy_summary_endpoint_returns_json():
    client = TestClient(app)
    response = client.get("/public/climate-energy-summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "indicators" in payload
    assert "earth_observation_layers" in payload
    assert "emissions_summary" in payload
