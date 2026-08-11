#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import Settings
from app.main import app
from app.release_health_v43531 import deployment_verification, source_health_policy
from app.version import APP_VERSION
from app.authoritative_connectors_v4354 import connector_catalog, connector_readiness
from app.authoritative_api_audit_v4354 import audit_overview

assert APP_VERSION == "4.35.5"
settings = Settings(_env_file=None, reliefweb_appname="")
verify = deployment_verification(settings)
assert verify["ok"] and verify["version"] == APP_VERSION
assert verify["source_health_blocks_release"] is False
assert verify["network_calls_performed"] is False
assert all(verify["checks"].values())
catalog = connector_catalog(settings)
assert catalog["connector_count"] == 10 and catalog["live_connector_count"] == 9
assert connector_readiness(settings)["ok"] is True
audit = audit_overview(settings)
assert len(audit["completed_connector_targets"]) == 10
assert audit["summary"]["registered_but_not_retrieved"] < 56
policy = source_health_policy(settings)
assert policy["ok"] and policy["summary"]["release_blocking_sources"] == 0
assert policy["network_calls_performed"] is False
client = TestClient(app)
for endpoint in (
    "/health",
    "/public/runtime-health",
    "/public/v4/readiness",
    "/public/authoritative-connectors/readiness",
    "/public/deployment-verification",
    "/public/source-health-policy",
    "/public/authoritative-connectors",
):
    r = client.get(endpoint)
    assert r.status_code == 200, endpoint
assert "/public/authoritative-connectors/noaa-coops/data" in (ROOT/"backend/app/main.py").read_text()
assert "/public/authoritative-connectors/noaa-ncei/data" in (ROOT/"backend/app/main.py").read_text()
assert "/public/authoritative-connectors/obis/occurrences" in (ROOT/"backend/app/main.py").read_text()
assert "/public/authoritative-connectors/eurostat/statistics" in (ROOT/"backend/app/main.py").read_text()
assert "/public/authoritative-connectors/usda-soils/mapunits" in (ROOT/"backend/app/main.py").read_text()
assert client.get("/public/v4/readiness").json()["summary"]["preserved_routes"] == 35
promotion=(ROOT/"promote_site_intelligence_v4_35_4_to_github_and_render_macos.sh").read_text()
assert "Deep gate:" not in promotion
assert "/public/deployment-verification" in promotion
assert "/public/source-health-policy" in promotion
assert "/public/climate/state" not in promotion
assert "External source availability is intentionally excluded" in promotion
render=(ROOT/"render.yaml").read_text()
assert "site-intelligence-v4.35.5" in render
print("PASS: v4.35.5 authoritative connector expansion II release contract")
