from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
checks={
"backend/app/version.py":["APP_VERSION = \"3.1.1\"","Connected Public Intelligence and Evidence Platform"],
"backend/app/live_intelligence_v310.py":["def build_live_intelligence","SCHEMA_VERSION"],
"backend/app/main.py":["/public/live-intelligence","/public/live-intelligence/status"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 3.1.1","sc_live_intelligence","astra_header_after","show_top_live_intelligence"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css":["Live Intelligence electronic ticker board","scsi-live-scroll"],
"wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js":["setupLiveIntelligence","/live-intelligence?limit="],
"README.md":["Current release:** v3.1.1 — Connected Public Intelligence and Evidence Platform"],
}
for rel,markers in checks.items():
 text=(ROOT/rel).read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text: raise SystemExit(f"{rel}: missing {marker}")
policy=json.loads((ROOT/"docs/RELEASE_MANIFEST_V310.json").read_text())
for key in ["public_safe_signal_contract","shortcode_available","astra_below_header_optional","top_ticker_can_be_disabled","duplicate_protection","source_attribution_required","freshness_required","reduced_motion_supported"]:
 if policy.get(key) is not True: raise SystemExit(f"Release policy requires {key}=true")
for key in ["raw_upstream_payloads_exposed","browser_api_keys_exposed","automatic_interpretation","sticky_ticker_default","sitewide_default"]:
 if policy.get(key) is not False: raise SystemExit(f"Release policy requires {key}=false")
print("Site Intelligence v3.1.1 release contract passed.")
