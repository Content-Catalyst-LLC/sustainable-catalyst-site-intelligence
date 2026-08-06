#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"backend"))
from app.main import app
required={
 "backend/app/version.py":["APP_VERSION = \"3.23.6.1\""],
 "backend/app/analytical_workspaces_v3234.py":["analytical-workspace-completion","cached_data_may_claim_live","VALID_STATES"],
 "backend/data/analytical_workspace_policy_v3234.json":["global_conditions","earth_observation","completion_gate"],
 "backend/public_app/index.html":["analytical-workspaces-v3234.css?v=3.23.6.1","analytical-workspaces-v3234.js?v=3.23.6.1"],
 "backend/public_app/service-worker.js":["const RELEASE=\"3.23.6.1\"","analytical-workspaces-v3234.js"],
 "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 3.23.6.1","analyticalWorkspacesJsUrl"],
 "RELEASE_NOTES_SITE_INTELLIGENCE_V3234.md":["Analytical Workspace Completion"],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file():raise SystemExit(f"Missing {rel}")
 text=p.read_text()
 for token in tokens:
  if token not in text:raise SystemExit(f"Missing {token!r} in {rel}")
payload=TestClient(app).get("/public/workflows/analytical").json()
if not payload.get("ok") or payload.get("version")!="3.23.6.1" or payload.get("workflow_count")!=5:raise SystemExit("Analytical workspace endpoint failed")
manifest=json.loads((ROOT/"MANIFEST.json").read_text()) if (ROOT/"MANIFEST.json").is_file() else None
if manifest and manifest.get("release")!="3.23.6.1":raise SystemExit("Manifest release mismatch")
print("Site Intelligence v3.23.6.1 analytical workspace release contract passed.")
