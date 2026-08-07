#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
required={
 'backend/app/version.py':['APP_VERSION = "3.25.0"'],
 'backend/app/data_truth_v3233.py':['data-freshness-coverage-and-source-truth','stale_marker_required','circuit_breaker_state'],
 'backend/public_app/index.html':['data-truth-v32371.css?v=3.25.0','data-truth-v32371.js?v=3.25.0'],
 'backend/public_app/service-worker.js':['const RELEASE="3.25.0"','data-truth-v32371.js'],
 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':['Version: 3.25.0','dataTruthJsUrl'],
 'RELEASE_NOTES_SITE_INTELLIGENCE_V3233.md':['Data Freshness, Coverage, and Source Truth'],
}
for rel,tokens in required.items():
 p=ROOT/rel
 if not p.is_file(): raise SystemExit(f'Missing {rel}')
 text=p.read_text()
 for token in tokens:
  if token not in text: raise SystemExit(f'Missing {token!r} in {rel}')
payload=TestClient(app).get('/public/data-truth').json()
if not payload.get('ok') or payload.get('version')!='3.25.0' or payload.get('source_count')!=8: raise SystemExit('Data truth endpoint failed')
manifest=json.loads((ROOT/'MANIFEST.json').read_text()) if (ROOT/'MANIFEST.json').is_file() else None
if manifest and manifest.get('release')!='3.25.0': raise SystemExit('Manifest release mismatch')
print('Site Intelligence v3.25.0 data truth release contract passed.')
