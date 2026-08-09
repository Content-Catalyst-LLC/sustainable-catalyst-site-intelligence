#!/usr/bin/env python3
from pathlib import Path
import json,sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "4.1.0"'],
 'backend/app/startup_stability_v32364.py':['public_startup_stability_contract'],
 'backend/data/startup_stability_policy_v32364.json':['production-soak-route-stability-and-service-worker-closure','background-all-settled'],
 'backend/public_app/assets/startup-stability-v32364.js':['HARD_FAIL_OPEN_MS=4500','scsi:shell-ready'],
 'backend/public_app/assets/app.js':['launchFinished','Promise.allSettled([layerTask,loadEvents(),loadCountry','routeTransitionActive'],
 'backend/public_app/assets/bootstrap-v32361.js':['automaticReloads:0','activateWaitingWorker','automaticReload:false'],
 'backend/public_app/service-worker.js':['SC_SI_GET_LIFECYCLE','event.waitUntil(installCritical())'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 4.1.0','loading="eager"','fetchpriority="high"'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V32364.md':['Production Soak, Route Stability, and Service-Worker Closure'],
}
for relative,tokens in required.items():
 p=ROOT/relative
 if not p.is_file():raise SystemExit(f'Missing {relative}')
 text=p.read_text(encoding='utf-8')
 for token in tokens:
  if token not in text:raise SystemExit(f'Missing {token!r} in {relative}')
client=TestClient(app)
contract=client.get('/public/startup-stability').json()
if not contract.get('ok') or contract.get('version')!='4.1.0':raise SystemExit('Startup-stability endpoint failed.')
health=client.get('/public/runtime-health').json();checks={row['id']:row for row in health.get('checks',[])}
if not health.get('ok') or checks.get('startup-stability-and-worker-closure',{}).get('status')!='pass':raise SystemExit('Runtime startup-stability check failed.')
manifest=ROOT/'MANIFEST.json'
if manifest.is_file() and json.loads(manifest.read_text()).get('release')!='4.1.0':raise SystemExit('Manifest release mismatch.')
print('Site Intelligence v4.1.0 production-soak, route-stability, and service-worker closure contract passed.')
