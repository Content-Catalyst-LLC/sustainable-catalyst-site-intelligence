#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "3.23.6.1"'],
 'backend/app/performance_offline_v3236.py':['performance-and-offline-recovery','public_performance_offline_contract'],
 'backend/data/performance_offline_policy_v3236.json':['first_useful_map_ms','network-first-timeout-cached-fallback','single_reload_guard'],
 'backend/public_app/index.html':['performance-offline-v3236.css?v=3.23.6.1','performance-offline-v3236.js?v=3.23.6.1'],
 'backend/public_app/service-worker.js':['const RELEASE="3.23.6.1"','cacheFirstImmutable','networkFirstData','X-SCSI-Data-State'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 3.23.6.1','performanceOfflineJsUrl'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V3236.md':['Performance and Offline Recovery'],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file():raise SystemExit(f'Missing {rel}')
 text=p.read_text()
 for token in tokens:
  if token not in text:raise SystemExit(f'Missing {token!r} in {rel}')
payload=TestClient(app).get('/public/performance-offline').json()
if not payload.get('ok') or payload.get('version')!='3.23.6.1' or payload.get('contract')!='performance-and-offline-recovery':raise SystemExit('Performance/offline endpoint failed')
health=TestClient(app).get('/public/runtime-health').json()
if not health.get('ok') or '/public/performance-offline' not in {x['path'] for x in health.get('endpoint_contracts',[])}:raise SystemExit('Runtime health performance contract failed')
manifest=json.loads((ROOT/'MANIFEST.json').read_text()) if (ROOT/'MANIFEST.json').is_file() else None
if manifest and manifest.get('release')!='3.23.6.1':raise SystemExit('Manifest release mismatch')
print('Site Intelligence v3.23.6.1 performance and offline recovery release contract passed.')
