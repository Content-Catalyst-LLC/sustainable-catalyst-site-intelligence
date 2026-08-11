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

assert APP_VERSION == "4.35.4"
settings = Settings(_env_file=None, reliefweb_appname="")
verify = deployment_verification(settings)
assert verify["ok"] and verify["version"] == APP_VERSION
assert verify["source_health_blocks_release"] is False
assert verify["network_calls_performed"] is False
assert all(verify["checks"].values())
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
):
    r = client.get(endpoint)
    assert r.status_code == 200, endpoint
assert client.get("/public/v4/readiness").json()["summary"]["preserved_routes"] == 35
promotion=(ROOT/"promote_site_intelligence_v4_35_3_1_to_github_and_render_macos.sh").read_text()
assert "Deep gate:" not in promotion
assert "/public/deployment-verification" in promotion
assert "/public/source-health-policy" in promotion
assert "/public/climate/state" not in promotion
assert "External source availability is intentionally excluded" in promotion
render=(ROOT/"render.yaml").read_text()
assert "site-intelligence-v4.35.4" in render
print("PASS: v4.35.4 deployment verification/source-health release contract")
