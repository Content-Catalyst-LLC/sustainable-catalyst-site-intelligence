#!/usr/bin/env python3
from pathlib import Path
import os
import sys
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.authoritative_api_audit_v4352 import ACCESS_CLASSES, audit_overview, audit_readiness, workspace_matrix
from app.config import Settings
from app.main import app
from app import unified_live_events
from app.version import APP_VERSION

assert APP_VERSION == "4.35.2"
settings = Settings(_env_file=None, reliefweb_appname="")
overview = audit_overview(settings)
summary = overview["summary"]
assert overview["ok"] and overview["version"] == "4.35.2"
assert summary["source_registrations"] >= 175
assert summary["unique_source_endpoints_or_records"] >= 100
assert summary["workspaces_with_source_registries"] >= 35
assert summary["machine_readable_registrations"] >= 80
assert summary["counts"]["REGISTERED"] > 0
assert tuple(ACCESS_CLASSES) == ("LIVE", "DISCOVERY", "REGISTERED", "AUTH_REQUIRED", "BULK", "STALE", "UNAVAILABLE")

matrix = workspace_matrix(settings)
assert matrix["ok"] and matrix["workspace_count"] >= 35
assert any(row["workspace"] == "Hydrology, Rivers, Flood & Drought" for row in matrix["workspaces"])
readiness = audit_readiness(settings)
assert readiness["ok"] and readiness["network_calls_performed"] is False
assert readiness["configuration"]["reliefweb_appname_configured"] is False

source = (ROOT / "backend/app/unified_live_events.py").read_text()
assert '"api_version": "v2"' in source
assert "https://api.reliefweb.int/v2/reports" in source
assert "api.reliefweb.int/v1/reports" not in source

old_appname = os.environ.pop("SC_SI_RELIEFWEB_APPNAME", None)
try:
    try:
        unified_live_events._reliefweb_reports()
    except RuntimeError as exc:
        assert str(exc) == "reliefweb_v2_appname_not_configured"
    else:
        raise AssertionError("ReliefWeb must not call V2 without configured appname")
finally:
    if old_appname is not None:
        os.environ["SC_SI_RELIEFWEB_APPNAME"] = old_appname

client = TestClient(app)
for endpoint in (
    "/public/authoritative-apis",
    "/public/authoritative-apis/workspaces",
    "/public/authoritative-apis/readiness",
):
    response = client.get(endpoint)
    assert response.status_code == 200, endpoint
    assert response.json().get("version") == "4.35.2", endpoint
catalog = client.get("/public/authoritative-apis/catalog", params={"workspace": "Hydrology"})
assert catalog.status_code == 200 and catalog.json().get("sources")
assert client.get("/public/authoritative-apis/catalog", params={"access_class": "INVALID"}).status_code == 400

print("PASS: v4.35.2 authoritative API/workspace integrity release contract")
