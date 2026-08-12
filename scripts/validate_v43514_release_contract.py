#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43514 import production_audit, production_readiness, closure_ledger
from app.authoritative_connectors_v43514 import connector_catalog, connector_readiness
assert APP_VERSION=='4.35.18'
settings=Settings(_env_file=None, reliefweb_appname='', hdx_hapi_app_identifier='', ipc_api_key='')
a=production_audit(settings)
assert a['production_controls_ready'] is True and a['coverage_closure_complete'] is False
assert a['machine_readable_summary']['registrations']==112
assert a['machine_readable_summary']['counts']['LIVE']==48
assert a['machine_readable_summary']['counts']['DISCOVERY']==13
assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==17
assert a['machine_readable_summary']['registered_not_retrieved']==32
assert a['machine_readable_summary']['implemented_discovery_or_configuration_gated']==78
assert a['machine_readable_summary']['counts']['STALE']==0
assert production_readiness(settings)['ok'] is True
ledger=closure_ledger(settings)
assert ledger['summary']['registered_not_retrieved']==32
rows={r['workspace']:r for r in ledger['workspace_ledger']}
assert rows['Agriculture, Crops & Food Systems']['registered_backlog']==0
assert rows['Humanitarian Intelligence']['registered_backlog']==0
c=connector_catalog(settings)
assert c['connector_count']==45 and c['live_connector_count']==28
assert c['discovery_connector_count']==9 and c['auth_required_connector_count']==8
r=connector_readiness(settings); assert r['ok'] is True and r['network_calls_performed'] is False
client=TestClient(app)
for endpoint in ('/public/authoritative-apis','/public/authoritative-apis/readiness','/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness','/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
    resp=client.get(endpoint); assert resp.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
for marker in ('authoritative_api_production_audit_v43514','authoritative_connectors_v43514','/public/authoritative-connectors/gdacs/events','/public/humanitarian/live/gdacs','/public/authoritative-connectors/hdx/datasets','/public/humanitarian/discovery/hdx','/public/authoritative-connectors/hdx-hapi','/public/food-security/live/hdx-hapi','/public/authoritative-connectors/ipc','/public/food-security/live/ipc','/public/authoritative-connectors/fews-net','/public/food-security/live/fews-net'):
    assert marker in main,marker
promotion=(ROOT/'promote_site_intelligence_v4_35_14_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
print('PASS: v4.35.18 High-Priority Workspace Connector Closure IV: Agriculture, Food Security & Humanitarian Conditions release contract')
