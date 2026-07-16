#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
CHECKS={
"backend/app/version.py":["2.23.0","Typed Cross-Platform Intelligence Workflows"],
"backend/app/config.py":["cross_platform_workflows_enabled","cross_platform_workflows_packets_path","cross_platform_workflows_queue_path"],
"backend/app/cross_platform_workflows_v2230.py":["class CrossPlatformWorkflowCenter","def create_packet(","def validate_packet(","def record_receipt(","def retry_failed(","def add_linkback("],
"backend/app/main.py":["/public/cross-platform-workflows","/admin/cross-platform-workflows/control-center","/admin/cross-platform-workflows/incoming"],
"backend/data/cross_platform_workflow_registry_v2230.json":["site-intelligence-to-workbench-analysis","research-lab-to-site-intelligence-result","platform-core-to-site-intelligence-status"],
"backend/data/cross_platform_workflow_policy_v2230.json":["automatic_remote_write","automatic_retry","public_packet_payloads"],
"backend/public_app/index.html":["data-route=\"workflows\"","id=\"crossPlatformWorkflowStudio\"","/app/assets/workflows-v2230.js?v=2.23.0"],
"backend/public_app/assets/app.js":["SCCrossPlatformWorkflowsV2230","route===\"workflows\""],
"backend/public_app/service-worker.js":["const RELEASE=\"2.23.0\"","/app/assets/workflows-v2230.js"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.23.0","sc_public_cross_platform_workflows","sc_cross_platform_workflows_control_center"],
"docs/RELEASE_MANIFEST_V2230.json":["typed_routes","automatic_remote_write","persistent_message_broker_included"],
"README.md":["Current release:** v2.23.0 — Typed Cross-Platform Intelligence Workflows","/app/?view=workflows"],
"CHANGELOG.md":["## 2.23.0 — Typed Cross-Platform Intelligence Workflows"],
}
errors=[]
for rel,markers in CHECKS.items():
 p=ROOT/rel
 if not p.exists(): errors.append(f"missing {rel}"); continue
 text=p.read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text: errors.append(f"{rel}: missing {marker}")
manifest=json.loads((ROOT/"docs/RELEASE_MANIFEST_V2230.json").read_text())
for key in ["required_field_validation","packet_provenance_required","sha256_receipts","bidirectional_handoffs","explicit_receipts","linkbacks","bounded_retries","human_retry_confirmation","platform_core_preferred_orchestrator"]:
 if manifest.get(key) is not True: errors.append(f"governance manifest {key} must be true")
for key in ["automatic_remote_write","automatic_retry","persistent_message_broker_included","account_provisioning","public_packet_payloads","individual_tracking","autonomous_consequential_actions"]:
 if manifest.get(key) is not False: errors.append(f"governance manifest {key} must be false")
for rel in manifest.get("writable_state_excluded",[]):
 if (ROOT/rel).exists(): errors.append(f"writable runtime directory packaged: {rel}")
if errors:
 print("Site Intelligence v2.23.0 release contract failed:",file=sys.stderr)
 for e in errors: print(f"- {e}",file=sys.stderr)
 raise SystemExit(1)
print("Site Intelligence v2.23.0 release contract passed.")
