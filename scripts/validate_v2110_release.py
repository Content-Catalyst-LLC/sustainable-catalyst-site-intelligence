from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
checks={
"backend/app/version.py":['APP_VERSION = "2.11.0"','RELEASE_NAME = "Public Data API, Embeds, and Institutional Integration"'],
"backend/app/public_data_api_embeds_v2110.py":["build_catalog","build_workspace_records","build_embed_manifest","build_institution_profile","build_workspace_csv"],
"backend/public_app/index.html":['data-route="integration"','id="publicDataIntegrationStudio"',"integration-v2110.js"],
"backend/public_app/assets/app.js":['const APP_VERSION="2.11.0"','route==="integration"',"SCIntegrationV2110"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.11.0","sc_public_data_api_integration","sc_site_intelligence_embed"],
"docs/RELEASE_MANIFEST_V2110.json":['"version": "2.11.0"','"provider_credentials_exposed": false','"paid_api_required": false'],
"README.md":["Current release:** v2.11.0","/app/?view=integration","/api/public/v1"],
}
for rel,needles in checks.items():
 p=r/rel
 if not p.exists():raise SystemExit(f"Missing {rel}")
 text=p.read_text()
 for n in needles:
  if n not in text:raise SystemExit(f"Missing contract marker {n} in {rel}")
print("Site Intelligence v2.11.0 release contract passed.")
