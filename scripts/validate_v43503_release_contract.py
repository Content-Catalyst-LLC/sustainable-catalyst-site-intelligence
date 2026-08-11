#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.authoritative_api_audit_v4353 import audit_overview, audit_readiness, source_inventory
from app.authoritative_connectors_v4353 import connector_catalog, connector_readiness
from app.config import Settings
from app.main import app
from app.version import APP_VERSION

assert APP_VERSION == "4.35.3"
settings = Settings(_env_file=None, reliefweb_appname="")
overview = audit_overview(settings)
summary = overview["summary"]
assert overview["ok"] and overview["version"] == "4.35.3"
assert summary["source_registrations"] >= 175
assert summary["machine_readable_registrations"] >= 90
assert summary["registered_but_not_retrieved"] <= 56
assert summary["stale_implemented_connectors"] == 0
assert len(overview["completed_connector_targets"]) == 5

rows = source_inventory(settings)
by_host = {}
for row in rows:
    by_host.setdefault(row.get("host"), set()).add(row["access_class"])
assert by_host["api.waterdata.usgs.gov"] == {"LIVE"}
assert by_host["coastwatch.noaa.gov"] == {"LIVE"}
assert by_host["exoplanetarchive.ipac.caltech.edu"] == {"LIVE"}
assert by_host["api.unhcr.org"] == {"LIVE"}
assert by_host["cmr.earthdata.nasa.gov"] == {"DISCOVERY"}
assert audit_readiness(settings)["ok"] is True

catalog = connector_catalog(settings)
assert catalog["connector_count"] == 5
assert catalog["live_connector_count"] == 4
assert catalog["discovery_connector_count"] == 1
ready = connector_readiness(settings)
assert ready["ok"] and ready["network_calls_performed"] is False

client = TestClient(app)
for endpoint in (
    "/public/authoritative-apis",
    "/public/authoritative-apis/workspaces",
    "/public/authoritative-apis/readiness",
    "/public/authoritative-connectors",
    "/public/authoritative-connectors/readiness",
):
    response = client.get(endpoint)
    assert response.status_code == 200, endpoint
    assert response.json().get("version") == "4.35.3", endpoint
assert client.get("/public/authoritative-apis/catalog", params={"access_class":"INVALID"}).status_code == 400

humanitarian = (ROOT / "backend/app/humanitarian_intelligence.py").read_text()
assert "https://api.reliefweb.int/v2" in humanitarian
assert "https://api.reliefweb.int/v1" not in humanitarian
render = (ROOT / "render.yaml").read_text()
assert "site-intelligence-v4.35.3" in render
assert "SC_SI_USGS_WATER_API_KEY" in render
print("PASS: v4.35.3 authoritative connector expansion release contract")
