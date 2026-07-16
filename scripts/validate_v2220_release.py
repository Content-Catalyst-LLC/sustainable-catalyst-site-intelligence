#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.22.0"', 'RELEASE_NAME = "Institutional Workspaces, Collaboration, and Review"'],
    "backend/app/config.py": ["institutional_workspaces_enabled", "institutional_workspaces_workspaces_path", "institutional_workspaces_retention_path"],
    "backend/app/institutional_workspaces_v2220.py": ['RELEASE_VERSION = "2.22.0"', "def create_workspace(", "def add_member(", "def save_assignment(", "def review_evidence(", "def retention_preview(", "def export_workspace("],
    "backend/app/main.py": ['"/public/institutional-workspaces"', '"/admin/institutional-workspaces/control-center"', '"/admin/institutional-workspaces/{workspace_id}/evidence-reviews"', '"/admin/institutional-workspaces/{workspace_id}/retention"'],
    "backend/data/institutional_workspaces_policy_v2220.json": ['"version": "2.22.0"', "Human approval", "do not replace an institutional identity provider", "automatic deletion"],
    "backend/public_app/index.html": ['data-route="workspaces"', 'id="institutionalWorkspaceStudio"', '/app/assets/workspaces-v2220.js?v=2.22.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.22.0"', 'workspaces:[', 'window.SCInstitutionalWorkspacesV2220'],
    "backend/public_app/assets/workspaces-v2220.js": ['const VERSION="2.22.0"', 'window.SCInstitutionalWorkspacesV2220', '/public/institutional-workspaces'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.22.0"', '"/app/assets/workspaces-v2220.css"', '"/app/assets/workspaces-v2220.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.22.0', 'sc_public_institutional_workspaces', 'sc_institutional_workspace', 'sc_institutional_workspaces_control_center'],
    "docs/V2220_INSTITUTIONAL_WORKSPACES_COLLABORATION_REVIEW.md": ["Public visitors never need an account", "Human approval", "confirm=true"],
    "docs/RELEASE_MANIFEST_V2220.json": ['"release": "2.22.0"', '"public_accounts_required": false', '"automatic_publication": false', '"retention_preview_required": true'],
    "README.md": ["Current release:** v2.22.0 — Institutional Workspaces, Collaboration, and Review", "/app/?view=workspaces"],
    "CHANGELOG.md": ["## 2.22.0 — Institutional Workspaces, Collaboration, and Review"],
}
errors=[]
for relative, markers in CHECKS.items():
    path=ROOT/relative
    if not path.exists():
        errors.append(f"missing {relative}")
        continue
    text=path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"{relative}: missing {marker}")
manifest=json.loads((ROOT/"docs/RELEASE_MANIFEST_V2220.json").read_text(encoding="utf-8"))
for key in ["human_evidence_review_required","retention_preview_required","file_backed_zero_cost_mode"]:
    if manifest.get(key) is not True: errors.append(f"governance manifest {key} must be true")
for key in ["public_accounts_required","persistent_authentication_included","automatic_publication","automatic_evidence_approval","individual_tracking","private_collaboration_records_public","remote_write_claimed"]:
    if manifest.get(key) is not False: errors.append(f"governance manifest {key} must be false")
for path in [
    ROOT/"backend/data/institutional_workspaces_v2220",
    ROOT/"backend/data/scheduled_monitoring_v2210",
    ROOT/"backend/data/intelligence_publishing_v2200",
    ROOT/"backend/data/knowledge_graph_v2190",
    ROOT/"backend/data/evidence_synthesis_v2180",
    ROOT/"backend/data/model_governance_v2170",
    ROOT/"backend/data/statistical_harmonization_v2160",
    ROOT/"backend/data/spatial_evidence_v2150",
    ROOT/"backend/data/historical_archive_v2140",
]:
    if path.exists(): errors.append(f"writable runtime directory packaged: {path.relative_to(ROOT)}")
if errors:
    print("Site Intelligence v2.22.0 release contract failed:", file=sys.stderr)
    for error in errors: print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)
print("Site Intelligence v2.22.0 release contract passed.")
