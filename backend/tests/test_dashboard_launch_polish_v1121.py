from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_launch_manifest():
    data = client.get("/public/dashboard-studio/launch-manifest").json()
    assert data["version"] == "3.21.0"
    assert data["release_status"] == "launch-ready"
    assert len(data["navigation"]) >= 6
    assert "stale" in data["public_states"]


def test_launch_readiness():
    data = client.get("/public/dashboard-studio/launch-readiness").json()
    assert data["counts"]["pass"] >= 7
    assert data["status"] == "launch-ready-with-production-qa"


def test_dashboard_has_launch_interaction_state():
    data = client.get("/public/dashboard-studio/climate-human-vulnerability/data").json()
    assert data["interaction_state"]["accessible_table"] is True
    assert data["data_state"] == "launch-ready-source-contract"
