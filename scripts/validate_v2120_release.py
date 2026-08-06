from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
checks={
"backend/app/version.py":['APP_VERSION = "2.12.0"','RELEASE_NAME = "Offline, Mobile, Accessibility, and Performance"'],
"backend/app/offline_mobile_accessibility_performance_v2120.py":["build_cache_plan","build_accessibility","build_performance","build_diagnostics"],
"backend/public_app/index.html":['data-route="experience"','id="offlineExperienceStudio"','rel="manifest"','experience-v2120.js'],
"backend/public_app/assets/app.js":['const APP_VERSION="2.12.0"','route==="experience"',"SCExperienceV2120"],
"backend/public_app/service-worker.js":["scsi-v2.12.0","/app/offline.html",'request.method !== "GET"'],
"backend/public_app/manifest.webmanifest":['"start_url": "/app/"','"display": "standalone"','icon-192.png'],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.12.0","sc_offline_mobile_accessibility_performance","'experience'"],
"docs/RELEASE_MANIFEST_V2120.json":['"version": "2.12.0"','"offline_freshness_guaranteed": false','"paid_api_required": false'],
"README.md":["Current release:** v2.12.0","/app/?view=experience","sc_offline_mobile_accessibility_performance"],
}
for rel,needles in checks.items():
 p=r/rel
 if not p.exists():raise SystemExit(f"Missing {rel}")
 text=p.read_text(encoding='utf-8')
 for n in needles:
  if n not in text:raise SystemExit(f"Missing contract marker {n} in {rel}")
manifest=json.loads((r/'backend/public_app/manifest.webmanifest').read_text(encoding='utf-8'))
if manifest.get('scope')!='/app/' or len(manifest.get('icons',[]))<2:raise SystemExit('PWA manifest is incomplete.')
print("Site Intelligence v2.12.0 release contract passed.")
