#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43516 import production_audit, production_readiness, closure_ledger
from app.authoritative_connectors_v43515 import connector_catalog, connector_readiness
from app.credential_configuration_v43516 import PROFILES, credential_registry, credential_readiness

assert APP_VERSION=='4.35.23'
settings=Settings(_env_file=None)
a=production_audit(settings)
assert a['production_controls_ready'] is True and a['coverage_closure_complete'] is False
assert a['machine_readable_summary']['registrations']==112
assert a['machine_readable_summary']['counts']['LIVE']==51
assert a['machine_readable_summary']['counts']['DISCOVERY']==15
assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==17
assert a['machine_readable_summary']['registered_not_retrieved']==27
assert a['machine_readable_summary']['counts']['BULK']==2
assert a['machine_readable_summary']['counts']['STALE']==0
assert production_readiness(settings)['ok'] is True
ledger=closure_ledger(settings); assert ledger['summary']['configuration_required']==17
cred=credential_registry(settings)
assert cred['profile_count']==12 and cred['mapped_auth_required_registrations']==17
assert cred['states']=={'configured':0,'missing':12,'partial':0,'invalid':0}
assert credential_readiness(settings)['ok'] is True and credential_readiness(settings)['configuration_complete'] is False
c=connector_catalog(settings)
assert c['connector_count']==50 and c['live_connector_count']==31 and c['discovery_connector_count']==11 and c['auth_required_connector_count']==8
assert connector_readiness(settings)['ok'] is True
client=TestClient(app)
for endpoint in ('/public/credential-configuration','/public/credential-configuration/readiness','/public/credential-configuration/workspaces','/public/authoritative-apis','/public/authoritative-apis/readiness','/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness','/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/deployment-verification','/public/source-health-policy'):
    resp=client.get(endpoint); assert resp.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
for marker in ('authoritative_api_production_audit_v43516','credential_configuration_v43516','release_health_v43516','/public/credential-configuration/readiness'):
    assert marker in main,marker
envs={env for p in PROFILES for _field,env,_kind in p['fields']}
for file in (ROOT/'render.yaml',ROOT/'backend/render.yaml'):
    text=file.read_text(); assert all(f'- key: {env}' in text for env in envs)
promotion=(ROOT/'promote_site_intelligence_v4_35_16_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
assert '/public/credential-configuration/readiness' in promotion
assert 'configuration_complete' not in promotion or 'credential_ready' in promotion
print('PASS: v4.35.23 Credentials, API-Key & Configuration Completion release contract')
