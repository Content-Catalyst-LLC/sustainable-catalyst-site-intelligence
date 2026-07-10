from fastapi.testclient import TestClient
from app.main import app
from app.planetary_boundaries_observatory import overview, boundary_detail, methodology

client = TestClient(app)

def test_overview_contains_nine_boundaries():
    payload = overview()
    assert payload["ok"] is True
    assert payload["counts"]["boundaries"] == 9
    assert payload["schema"] == "sc-planetary-boundaries-observatory/1.0"
    assert all("scientific_status" in row for row in payload["boundaries"])


def test_detail_separates_reference_from_live_assessment():
    payload = boundary_detail("climate-change")
    assert payload["boundary"]["is_live_assessment"] is False
    assert payload["boundary"]["scientific_status"] == "official_assessment_reference"
    assert payload["boundary"]["control_variables"]


def test_methodology_has_governance_rules():
    payload = methodology()
    assert len(payload["methodology"]) >= 5
    assert payload["references"]


def test_public_endpoints():
    assert client.get("/public/planetary-boundaries").status_code == 200
    assert client.get("/public/planetary-boundaries/climate-change").status_code == 200
    assert client.get("/public/planetary-boundaries/climate-change/trend").status_code == 200
    assert client.get("/public/planetary-boundaries/methodology").status_code == 200
    assert client.get("/public/planetary-boundaries/export").status_code == 200
    assert client.get("/public/planetary-boundaries/not-a-boundary").status_code == 404
