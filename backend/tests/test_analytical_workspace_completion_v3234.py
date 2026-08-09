from __future__ import annotations
from pathlib import Path
from fastapi.testclient import TestClient
from app.analytical_workspaces_v3234 import AnalyticalWorkspaceCenter
from app.config import Settings
from app.main import app
ROOT=Path(__file__).resolve().parents[2]
CLIENT=TestClient(app)
def read(path: str) -> str: return (ROOT/path).read_text(encoding="utf-8")

def test_directory_declares_five_operational_exportable_workflows():
    payload=CLIENT.get("/public/workflows/analytical").json()
    assert payload["ok"] is True and payload["version"]=="4.4.0"
    assert payload["release_id"]=="site-intelligence-v4.4.0"
    assert payload["contract"]=="analytical-workspace-completion"
    assert payload["workflow_count"]==5 and payload["summary"]=={"operational":5,"limited":0,"unavailable":0}
    assert {w["workflow_id"] for w in payload["workflows"]}=={"global_conditions","country_intelligence","compare","spatial_evidence","earth_observation"}
    assert all(w["completion"]["states_complete"] and w["completion"]["export_declared"] for w in payload["workflows"])

def test_each_workflow_has_complete_state_and_boundary_contract():
    for workflow_id in ("global_conditions","country_intelligence","compare","spatial_evidence","earth_observation"):
        response=CLIENT.get(f"/public/workflows/analytical/{workflow_id}")
        assert response.status_code==200
        row=response.json()["workflow"]
        assert row["runtime_states"]==["initial","ready","empty","degraded","unavailable"]
        assert row["empty_state"] and row["degraded_state"] and row["source_truth_endpoint"]=="/public/data-truth"
        assert row["deep_link"].startswith("/app/?view=") and row["supporting_endpoints"]

def test_unknown_workflow_fails_closed():
    assert CLIENT.get("/public/workflows/analytical/not-real").status_code==404
    assert CLIENT.get("/public/workflows/analytical/not-real/snapshot").status_code==404

def test_snapshot_preserves_non_live_boundaries_with_injected_provider():
    providers={
      "earth_overview":lambda:{"status":"ready"},"earth_layers":lambda:{"layers":[{"id":"true-color"}]},
      "earth_presets":lambda:{"presets":[]},"earth_diagnostics":lambda:{"ok":True},
    }
    payload=AnalyticalWorkspaceCenter(Settings(),providers=providers).snapshot("earth_observation",{})
    assert payload["state"]["state"]=="ready"
    assert payload["boundaries"]["cached_data_may_claim_live"] is False
    assert payload["boundaries"]["missing_values_imputed"] is False

def test_app_shell_and_service_worker_package_workflow_assets_inside_app_only():
    html=read("backend/public_app/index.html")
    assert "/app/assets/analytical-workspaces-v3234.css?v=4.4.0" in html
    assert "/app/assets/analytical-workspaces-v3234.js?v=4.4.0" in html
    assert html.index("analytical-workspaces-v3234.js") < html.index("data-truth-v32371.js") < html.index("production-truth-v3231.js")
    js=read("backend/public_app/assets/analytical-workspaces-v3234.js")
    for token in ("analyticalWorkflowToggle","Five complete public workflows","scsi:analytical-workspaces-ready","insideApp"):
        assert token in js
    worker=read("backend/public_app/service-worker.js")
    assert "analytical-workspaces-v3234.js" in worker and "analytical-workspaces-v3234.css" in worker
    php=read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "analyticalWorkspacesJsUrl" in php and "Version: 4.4.0" in php
    assert "wp_enqueue_script('scsi-analytical-workspaces'" not in php
    assert (ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/assets/analytical-workspaces-v3234.js").is_file()

def test_runtime_health_covers_workflow_endpoint_and_assets():
    health=CLIENT.get("/public/runtime-health").json()
    assets={row["path"] for row in health["assets"]}; endpoints={row["path"] for row in health["endpoint_contracts"]}
    assert "/app/assets/analytical-workspaces-v3234.js" in assets
    assert "/app/assets/analytical-workspaces-v3234.css" in assets
    assert "/public/workflows/analytical" in endpoints
