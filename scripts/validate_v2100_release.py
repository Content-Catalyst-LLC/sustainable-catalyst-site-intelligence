from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
checks={
"backend/app/version.py":['APP_VERSION = "2.10.0"','RELEASE_NAME = "Research Paths, Saved Investigations, and Briefing Workflows"'],
"backend/app/research_paths_investigations_v2100.py":["INVESTIGATION_SCHEMA","build_briefing_packet","build_product_handoff"],
"backend/public_app/index.html":['data-route="research"','id="researchWorkflowStudio"',"research-v2100.js"],
"backend/public_app/assets/app.js":['const APP_VERSION="2.10.0"','route==="research"',"SCResearchV2100"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.10.0","sc_research_paths_investigations"],
"docs/RELEASE_MANIFEST_V2100.json":['"version": "2.10.0"','"server_persistence": false','"paid_api_required": false'],
"README.md":["Current release:** v2.10.0","/app/?view=research"],
}
for rel,needles in checks.items():
 p=r/rel
 if not p.exists():raise SystemExit(f"Missing {rel}")
 text=p.read_text()
 for n in needles:
  if n not in text:raise SystemExit(f"Missing contract marker {n} in {rel}")
print("Site Intelligence v2.10.0 release contract passed.")
