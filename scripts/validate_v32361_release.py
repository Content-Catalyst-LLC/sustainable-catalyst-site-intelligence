#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "4.15.0"'],
 'backend/app/bootstrap_recovery_v32361.py':['Single-owner bootstrap','public_bootstrap_recovery_contract'],
 'backend/data/bootstrap_recovery_policy_v32361.json':['single-owner-bootstrap-and-loading-recovery','registration_owner_count'],
 'backend/public_app/index.html':['bootstrap-v32361.js?v=4.15.0','data-scsi-startup-deadline-ms="9000"'],
 'backend/public_app/assets/bootstrap-v32361.js':['serviceWorker.register','startup deadline exceeded','scsi:application-ready'],
 'backend/public_app/assets/app.js':['async function startApplication()','Application startup recovered','scsi:application-ready'],
 'backend/public_app/service-worker.js':['const RELEASE="4.15.0"','bootstrap-v32361.js'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 4.15.0'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V32361.md':['Single-Owner Bootstrap and Loading Recovery'],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file():raise SystemExit(f'Missing {rel}')
 text=p.read_text()
 for token in tokens:
  if token not in text:raise SystemExit(f'Missing {token!r} in {rel}')
assets=ROOT/'backend/public_app/assets'
registrations=[];controllers=[]
for p in assets.glob('*.js'):
 text=p.read_text()
 if 'serviceWorker.register' in text:registrations.append(p.name)
 if 'controllerchange' in text:controllers.append(p.name)
if registrations!=['bootstrap-v32361.js'] or controllers!=['bootstrap-v32361.js']:
 raise SystemExit(f'Service-worker ownership mismatch: {registrations=} {controllers=}')
client=TestClient(app)
bootstrap=client.get('/public/bootstrap-recovery').json()
if not bootstrap.get('ok') or bootstrap.get('version')!='4.15.0' or bootstrap.get('service_worker',{}).get('registration_owner_count')!=1:raise SystemExit('Bootstrap endpoint failed')
health=client.get('/public/runtime-health').json()
if not health.get('ok') or '/public/bootstrap-recovery' not in {x['path'] for x in health.get('endpoint_contracts',[])}:raise SystemExit('Runtime health bootstrap contract failed')
manifest=json.loads((ROOT/'MANIFEST.json').read_text()) if (ROOT/'MANIFEST.json').is_file() else None
if manifest and manifest.get('release')!='4.15.0':raise SystemExit('Manifest release mismatch')
print('Site Intelligence v4.15.0 single-owner bootstrap and loading recovery release contract passed.')
