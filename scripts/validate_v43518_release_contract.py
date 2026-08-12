#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43516 import production_audit
from app.authoritative_connectors_v43515 import connector_catalog
from app.credential_configuration_v43516 import credential_readiness
from app.external_resilience_v43517 import resilience_readiness
from app.release_health_v43518 import deployment_verification, source_health_policy
from app.workspace_browser_audit_v43518 import workspace_browser_audit, workspace_browser_readiness

assert APP_VERSION == "4.35.21"
settings = Settings(_env_file=None)

audit = workspace_browser_audit()
ready = workspace_browser_readiness()
assert audit["ok"] is True
assert audit["route_count"] == 35
assert audit["primary_area_count"] == 6
assert len(audit["routes"]) == 35
assert all(audit["checks"].values())
assert ready["ok"] is True
assert ready["network_calls_performed"] is False
assert ready["upstream_health_release_blocking"] is False

# This browser/reliability release does not reclassify connector coverage.
prod = production_audit(settings)["machine_readable_summary"]
assert prod["registrations"] == 112
assert prod["counts"]["LIVE"] == 51
assert prod["counts"]["DISCOVERY"] == 15
assert prod["counts"]["AUTH_REQUIRED"] == 17
assert prod["registered_not_retrieved"] == 27
assert prod["counts"]["BULK"] == 2
assert prod["counts"]["STALE"] == 0
catalog = connector_catalog(settings)
assert catalog["connector_count"] == 50
assert catalog["live_connector_count"] == 31
assert catalog["discovery_connector_count"] == 11
assert catalog["auth_required_connector_count"] == 8
assert credential_readiness(settings)["ok"] is True
assert resilience_readiness(settings)["ok"] is True

verification = deployment_verification(settings)
assert verification["ok"] is True
assert verification["checks"]["workspace_browser_control_plane_ready"] is True
assert verification["checks"]["all_35_registered_routes_audited"] is True
assert verification["checks"]["registered_routes_have_recovery_surface"] is True
assert verification["checks"]["browser_provider_health_non_blocking"] is True
assert "/public/workspace-browser-audit/readiness" in verification["required_routes"]
assert len(verification["required_routes"]) == 10
health = source_health_policy(settings)
assert health["workspace_browser_reliability"]["blank_registered_routes_allowed"] is False
assert health["workspace_browser_reliability"]["explicit_degraded_state_required"] is True
assert health["workspace_browser_reliability"]["upstream_health_release_blocking"] is False

client = TestClient(app)
for endpoint in (
    "/public/workspace-browser-audit",
    "/public/workspace-browser-audit/readiness",
    "/public/workspace-browser-audit/route/overview",
    "/public/workspace-browser-audit/route/workflows",
    "/public/deployment-verification",
    "/public/source-health-policy",
    "/public/external-resilience/readiness",
):
    response = client.get(endpoint)
    assert response.status_code == 200, endpoint

main=(ROOT/"backend/app/main.py").read_text()
for marker in ("workspace_browser_audit_v43518", "release_health_v43518", "/public/workspace-browser-audit/readiness"):
    assert marker in main, marker
app_js=(ROOT/"backend/public_app/assets/app.js").read_text()
rel_js=(ROOT/"backend/public_app/assets/workspace-reliability-v43518.js").read_text()
index=(ROOT/"backend/public_app/index.html").read_text()
css=(ROOT/"backend/public_app/assets/app.css").read_text()
for marker in ("SCSIWorkspaceReliabilityV43518?.enforce", "registered route recovery", "Move evidence between products without losing context"):
    assert marker in app_js, marker
for marker in ("workspace-recovery", "Retry workspace", "Sources & methods"):
    assert marker in rel_js, marker
assert "workspace-reliability-v43518.js" in index
assert "SIMPLY WORKS WORKSPACE AUDIT" in index
assert "html,body,#app,#main{max-width:100%;overflow-x:hidden}" in css

promotion=(ROOT/"promote_site_intelligence_v4_35_18_to_github_and_render_macos.sh").read_text()
assert "Deep gate:" not in promotion
assert "/public/workspace-browser-audit/readiness" in promotion
assert "workspace_browser_ready" in promotion
print("PASS: v4.35.21 Full Workspace End-to-End Browser Audit & Simply Works Reliability release contract")
