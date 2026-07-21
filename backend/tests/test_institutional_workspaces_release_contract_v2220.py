from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.7.0"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/institutional_workspaces_v2220.py": ['RELEASE_VERSION = "3.7.0"', "def create_workspace(", "def add_member(", "def review_evidence(", "def export_workspace("],
        "backend/public_app/index.html": ['data-route="workspaces"', 'id="institutionalWorkspaceStudio"'],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 3.7.0', 'sc_public_institutional_workspaces', 'sc_institutional_workspaces_control_center'],
        "README.md": ["Current release:** v3.7.0 — Connected Public Intelligence and Evidence Platform"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{relative}: {marker}"


def test_governance_manifest_blocks_unsafe_claims():
    data = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2220.json").read_text(encoding="utf-8"))
    assert data["human_evidence_review_required"] is True
    assert data["retention_preview_required"] is True
    assert data["public_accounts_required"] is False
    assert data["persistent_authentication_included"] is False
    assert data["automatic_publication"] is False
    assert data["automatic_evidence_approval"] is False
    assert data["private_collaboration_records_public"] is False
    assert data["individual_tracking"] is False


def test_service_worker_and_app_include_workspace_assets():
    sw = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    app = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'const RELEASE="3.7.0"' in sw
    assert '"/app/assets/workspaces-v2220.css"' in sw
    assert '"/app/assets/workspaces-v2220.js"' in sw
    assert "window.SCInstitutionalWorkspacesV2220" in app
