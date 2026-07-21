from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.unified_live_events import unified_events, categories_summary

client = TestClient(app)

def test_root_reports_v1170():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "3.7.1"

@patch("app.unified_live_events._usgs_events", return_value=[])
@patch("app.unified_live_events._eonet_events", return_value=[])
@patch("app.unified_live_events._reliefweb_reports", return_value=[])
def test_events_fall_back_when_sources_empty(reliefweb, eonet, usgs):
    payload = unified_events(days=7)
    assert payload["data_state"] == "fallback"
    assert payload["count"] >= 1
    assert all(item["data_state"] == "fallback" for item in payload["events"])

def test_public_event_endpoints():
    with patch("app.unified_live_events._usgs_events", return_value=[]), \
         patch("app.unified_live_events._eonet_events", return_value=[]), \
         patch("app.unified_live_events._reliefweb_reports", return_value=[]):
        response = client.get("/public/events?days=7")
        assert response.status_code == 200
        assert "events" in response.json()

        categories = client.get("/public/events/categories?days=7")
        assert categories.status_code == 200
        assert "categories" in categories.json()

        summary = client.get("/public/events/summary?days=7")
        assert summary.status_code == 200
        assert "event_count" in summary.json()

def test_event_app_assets_present():
    base = Path(__file__).resolve().parents[1] / "public_app"
    html = (base / "index.html").read_text()
    css = (base / "assets" / "app.css").read_text()
    js = (base / "assets" / "app.js").read_text()
    assert "eventStudio" in html
    assert "event-studio-layout" in css
    assert "openEventStudio" in js
    assert "openEventDrawer" in js
