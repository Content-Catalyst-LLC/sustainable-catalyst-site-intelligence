from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]

from app.config import Settings
from app.main import app
from app.release_health_v43518 import deployment_verification, source_health_policy
from app.workspace_browser_audit_v43518 import ROUTE_SURFACES, workspace_browser_audit, workspace_browser_readiness, workspace_route_detail


def test_workspace_audit_covers_all_35_routes():
    audit = workspace_browser_audit()
    assert audit["ok"] is True
    assert audit["route_count"] == 35
    assert audit["primary_area_count"] == 6
    assert len(ROUTE_SURFACES) == 35
    assert all(row["surface_declared"] for row in audit["routes"])
    assert all(row["route_metadata_declared"] for row in audit["routes"])
    assert all(row["router_branch_declared"] for row in audit["routes"])


def test_registered_routes_have_explicit_recovery_contract():
    audit = workspace_browser_audit()
    assert audit["checks"]["recovery_layer_present"] is True
    assert audit["checks"]["view_unavailable_not_used_for_registered_routes"] is True
    assert audit["simply_works_definition"]["registered_route_never_blank"] is True
    assert audit["simply_works_definition"]["explicit_degraded_state_when_module_or_data_fails"] is True


def test_route_detail_is_deterministic_and_unknown_route_is_rejected():
    assert workspace_route_detail("overview")["surface_selector"] == "#map"
    assert workspace_route_detail("sources")["surface_selector"] == "#sourceStudio"
    try:
        workspace_route_detail("not-a-workspace")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown route must fail")


def test_readiness_is_network_free_and_provider_health_non_blocking():
    ready = workspace_browser_readiness()
    assert ready["ok"] is True
    assert ready["network_calls_performed"] is False
    assert ready["upstream_health_release_blocking"] is False


def test_deployment_verification_requires_workspace_browser_control_plane():
    verification = deployment_verification(Settings(_env_file=None))
    assert verification["ok"] is True
    assert verification["checks"]["workspace_browser_control_plane_ready"] is True
    assert verification["checks"]["all_35_registered_routes_audited"] is True
    assert verification["checks"]["registered_routes_have_recovery_surface"] is True
    assert verification["checks"]["browser_provider_health_non_blocking"] is True
    assert "/public/workspace-browser-audit/readiness" in verification["required_routes"]
    assert len(verification["required_routes"]) == 10


def test_source_health_keeps_browser_provider_health_non_blocking():
    health = source_health_policy(Settings(_env_file=None))
    browser = health["workspace_browser_reliability"]
    assert browser["route_count"] == 35
    assert browser["blank_registered_routes_allowed"] is False
    assert browser["explicit_degraded_state_required"] is True
    assert browser["upstream_health_release_blocking"] is False


def test_public_audit_endpoints():
    client = TestClient(app)
    for path in ("/public/workspace-browser-audit", "/public/workspace-browser-audit/readiness", "/public/workspace-browser-audit/route/overview", "/public/workspace-browser-audit/route/sources"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["ok"] is True
    assert client.get("/public/workspace-browser-audit/route/not-a-workspace").status_code == 404


def test_frontend_enforces_recovery_after_every_route_transition():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    reliability = (ROOT / "backend/public_app/assets/workspace-reliability-v43518.js").read_text(encoding="utf-8")
    index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert "SCSIWorkspaceReliabilityV43518?.enforce" in js
    assert "SCSIWorkspaceReliabilityV43518?.enforce?.(current,error?.message" in js
    assert "registered route recovery" in js
    assert "workspace-recovery" in reliability
    assert "Retry workspace" in reliability
    assert "Sources & methods" in reliability
    assert "workspace-reliability-v43518.js" in index
    assert "SIMPLY WORKS WORKSPACE AUDIT" in index
