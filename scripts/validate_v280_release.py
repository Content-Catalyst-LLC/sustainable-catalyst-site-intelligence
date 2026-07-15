from pathlib import Path
import json
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]).resolve()
required={
 "backend/app/version.py":['APP_VERSION = "2.8.0"','RELEASE_NAME = "Alerts, Monitoring, and Live Intelligence Streams"'],
 "backend/app/alerts_monitoring_live_streams.py":["build_stream_snapshot","evaluate_alert_rules","build_source_watch","build_sse_snapshot","rules_persisted_server_side"],
 "backend/app/main.py":["/public/live-intelligence-stream/events","/public/alerts-monitoring/evaluate","/public/alerts-monitoring/diagnostics"],
 "backend/public_app/index.html":['data-route="alerts"','id="alertsStudio"','alerts-v280.js','No server-side user tracking'],
 "backend/public_app/assets/app.js":['const APP_VERSION="2.8.0"','route==="alerts"','SCAlertsV280'],
 "backend/public_app/assets/alerts-v280.js":["SCAlertsV280","EventSource","sc_site_intelligence_alert_rules_v280"],
 "backend/public_app/assets/alerts-v280.css":[".alerts-studio",".alerts-stream"],
 "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.8.0","sc_alerts_monitoring_live_intelligence"],
 "docs/RELEASE_MANIFEST_V280.json":['"version": "2.8.0"','"paid_api_required": false','"server_side_user_tracking": false'],
 "backend/tests/test_alerts_monitoring_live_streams_v280.py":["test_stream_snapshot_preserves_sources_and_no_fabrication","test_public_routes"],
 "CHANGELOG.md":["2.8.0","Alerts, Monitoring, and Live Intelligence Streams"],
 "README.md":["Current release:** v2.8.0","/app/?view=alerts"],
}
missing=[]
for relative,markers in required.items():
 path=root/relative
 if not path.is_file():missing.append(f"missing file: {relative}");continue
 text=path.read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text:missing.append(f"missing marker in {relative}: {marker}")
manifest=json.loads((root/'docs/RELEASE_MANIFEST_V280.json').read_text(encoding='utf-8'))
for key in ('paid_api_required','fabricated_fallback','server_side_user_tracking','operational_emergency_alert','individual_risk_scoring','investment_signal','legal_determination','military_targeting'):
 if manifest.get(key) is not False:missing.append(f"release manifest must set {key}=false")
if missing:raise SystemExit('\n'.join(missing))
print('Site Intelligence v2.8.0 release contract passed.')
