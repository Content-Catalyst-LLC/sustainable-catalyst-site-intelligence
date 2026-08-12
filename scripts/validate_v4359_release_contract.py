#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v4359 import production_audit, production_readiness, closure_ledger
assert APP_VERSION=='4.35.13'
settings=Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')
a=production_audit(settings)
assert a['production_controls_ready'] is True
assert a['coverage_closure_complete'] is False
assert a['machine_readable_summary']['registrations']==101
assert a['machine_readable_summary']['registered_not_retrieved']==44
assert a['machine_readable_summary']['implemented_discovery_or_configuration_gated']==53
assert a['summary']['counts']['STALE']==0
assert production_readiness(settings)['ok'] is True
assert closure_ledger(settings)['summary']['registered_not_retrieved']==44
client=TestClient(app)
for endpoint in ('/public/authoritative-apis','/public/authoritative-apis/readiness','/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness','/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
 r=client.get(endpoint); assert r.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
assert 'authoritative_api_production_audit_v4359' in main
promotion=(ROOT/'promote_site_intelligence_v4_35_9_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
print('PASS: v4.35.13 Authoritative API Coverage Closure & Production Audit release contract')
