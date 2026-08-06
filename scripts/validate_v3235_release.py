#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "3.23.6"'],
 'backend/app/browser_reliability_v3235.py':['browser-reliability-mobile-accessibility','public_browser_reliability_contract'],
 'backend/data/browser_reliability_policy_v3235.json':['route_focus_management','low_bandwidth_mode','minimum_touch_target_px'],
 'backend/public_app/index.html':['browser-reliability-v3235.css?v=3.23.6','browser-reliability-v3235.js?v=3.23.6'],
 'backend/public_app/service-worker.js':['const RELEASE="3.23.6"','browser-reliability-v3235.js'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 3.23.6','browserReliabilityJsUrl'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V3235.md':['Browser Reliability, Mobile, and Accessibility'],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file():raise SystemExit(f'Missing {rel}')
 text=p.read_text()
 for token in tokens:
  if token not in text:raise SystemExit(f'Missing {token!r} in {rel}')
payload=TestClient(app).get('/public/browser-reliability').json()
if not payload.get('ok') or payload.get('version')!='3.23.6' or payload.get('contract')!='browser-reliability-mobile-accessibility':raise SystemExit('Browser reliability endpoint failed')
manifest=json.loads((ROOT/'MANIFEST.json').read_text()) if (ROOT/'MANIFEST.json').is_file() else None
if manifest and manifest.get('release')!='3.23.6':raise SystemExit('Manifest release mismatch')
print('Site Intelligence v3.23.6 browser reliability release contract passed.')
