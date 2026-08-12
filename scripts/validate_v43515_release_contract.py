#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43515 import production_audit, production_readiness, closure_ledger
from app.authoritative_connectors_v43515 import connector_catalog, connector_readiness
assert APP_VERSION=='4.35.17'
settings=Settings(_env_file=None, reliefweb_appname='', hdx_hapi_app_identifier='', ipc_api_key='')
a=production_audit(settings)
assert a['production_controls_ready'] is True and a['coverage_closure_complete'] is False
assert a['machine_readable_summary']['registrations']==112
assert a['machine_readable_summary']['counts']['LIVE']==51
assert a['machine_readable_summary']['counts']['DISCOVERY']==15
assert a['machine_readable_summary']['counts']['AUTH_REQUIRED']==17
assert a['machine_readable_summary']['registered_not_retrieved']==27
assert a['machine_readable_summary']['implemented_discovery_or_configuration_gated']==83
assert a['machine_readable_summary']['counts']['STALE']==0
assert production_readiness(settings)['ok'] is True
ledger=closure_ledger(settings)
assert ledger['summary']['registered_not_retrieved']==27
rows={r['workspace']:r for r in ledger['workspace_ledger']}
assert rows['Mining & Critical Materials']['registered_backlog']==0
assert rows['Industrial Manufacturing & Trade']['registered_backlog']==0
c=connector_catalog(settings)
assert c['connector_count']==50 and c['live_connector_count']==31
assert c['discovery_connector_count']==11 and c['auth_required_connector_count']==8
r=connector_readiness(settings); assert r['ok'] is True and r['network_calls_performed'] is False
client=TestClient(app)
for endpoint in ('/public/authoritative-apis','/public/authoritative-apis/readiness','/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness','/public/authoritative-connectors','/public/authoritative-connectors/readiness','/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
    resp=client.get(endpoint); assert resp.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
for marker in ('authoritative_api_production_audit_v43515','authoritative_connectors_v43515','/public/authoritative-connectors/osm-mining','/public/mining-critical-materials/live/osm-mining','/public/authoritative-connectors/usgs-usmin/discovery','/public/mining-critical-materials/discovery/usgs-usmin','/public/authoritative-connectors/usgs-mcs-2026/discovery','/public/mining-critical-materials/discovery/usgs-mcs-2026','/public/authoritative-connectors/osm-industrial','/public/industrial-manufacturing/live/osm-industrial','/public/authoritative-connectors/wits/trade-stats','/public/industrial-manufacturing/live/wits'):
    assert marker in main,marker
promotion=(ROOT/'promote_site_intelligence_v4_35_15_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
print('PASS: v4.35.17 High-Priority Workspace Connector Closure V: Mining, Critical Materials & Industrial Systems release contract')
