#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/production-assurance');assert s.status_code==200;s=s.json();assert s['version']=='3.31.0' and s['contract']=='security-observability-performance-scale-assurance' and s['summary']['default_token_allowed'] is False
sec=c.get('/public/production-assurance/security').json();assert sec['production_fail_closed'] is True and sec['admin_rate_limit']['distributed'] is False
perf=c.get('/public/production-assurance/performance').json();assert perf['ok'] is True
supply=c.get('/public/production-assurance/supply-chain').json();assert supply['hash_pinning_claimed'] is False
smoke=c.post('/public/production-assurance/post-deploy/preview',json={'release':'3.31.0','commit':'expected'}).json();assert smoke['preview']['network_requests_performed'] is False
html=(BACKEND/'public_app/index.html').read_text();worker=(BACKEND/'public_app/service-worker.js').read_text();js=(BACKEND/'public_app/assets/security-performance-v3310.js').read_text();assert 'security-performance-v3310.js?v=3.31.0' in html and 'security-performance-v3310.js' in worker and 'SCSIProductionAssuranceV3310' in js
print(json.dumps({'version':s['version'],'assurance_sha256':s['assurance_sha256'],'performance_ok':perf['ok'],'security_fail_closed':sec['production_fail_closed']},indent=2));print('PASS: Site Intelligence v3.31.0 Security, Observability, Performance, and Scale Assurance contracts are complete.')
