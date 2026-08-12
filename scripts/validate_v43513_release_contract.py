#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43513 import production_audit, production_readiness, closure_ledger
from app.authoritative_connectors_v43513 import connector_catalog, connector_readiness
assert APP_VERSION=='4.35.19'
settings=Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')
a=production_audit(settings)
assert a['production_controls_ready'] is True
assert a['coverage_closure_complete'] is False
assert a['machine_readable_summary']['registrations']==108
assert a['machine_readable_summary']['counts']['LIVE']==46
assert a['machine_readable_summary']['registered_not_retrieved']==34
assert a['machine_readable_summary']['implemented_discovery_or_configuration_gated']==72
assert a['machine_readable_summary']['counts']['STALE']==0
assert production_readiness(settings)['ok'] is True
assert closure_ledger(settings)['summary']['registered_not_retrieved']==34
ledger=closure_ledger(settings)
rows={r['workspace']:r for r in ledger['workspace_ledger']}
assert rows['Hydrology, Rivers, Flood & Drought']['registered_backlog']==0
assert rows['Water, Wastewater & Sanitation']['registered_backlog']==0
c=connector_catalog(settings)
assert c['connector_count']==40 and c['live_connector_count']==26
assert c['discovery_connector_count']==8 and c['auth_required_connector_count']==6
r=connector_readiness(settings)
assert r['ok'] is True and r['network_calls_performed'] is False
client=TestClient(app)
for endpoint in (
 '/public/authoritative-apis','/public/authoritative-apis/readiness','/public/authoritative-apis/production-audit',
 '/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness',
 '/public/authoritative-connectors','/public/authoritative-connectors/readiness',
 '/public/evidence-intelligence/readiness','/public/workspace-evidence/readiness'):
 resp=client.get(endpoint); assert resp.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
for marker in ('authoritative_api_production_audit_v43513','authoritative_connectors_v43513','/public/authoritative-connectors/faostat/data','/public/authoritative-connectors/ilostat/indicator','/public/authoritative-connectors/oecd/sdmx','/public/authoritative-connectors/epa-frs/facilities','/public/authoritative-connectors/usgs-volcano/notices','/public/energy-systems/live/osm-power','/public/energy-systems/live/eia','/public/energy-systems/live/ember','/public/energy-systems/live/entsoe','/public/digital-connectivity/live/osm-telecom','/public/digital-connectivity/discovery/mlab','/public/digital-connectivity/discovery/fcc-bdc','/public/authoritative-connectors/airnow/current','/public/atmosphere/live/airnow','/public/authoritative-connectors/copernicus-era5/catalogue','/public/climate/discovery/era5','/public/authoritative-connectors/cams/catalogue','/public/atmosphere/discovery/cams','/public/authoritative-connectors/osm-water','/public/water-sanitation/live/osm-water','/public/authoritative-connectors/epa-sdwis','/public/water-sanitation/live/epa-sdwis','/public/authoritative-connectors/nidis-drought/file','/public/hydrology/live/drought-gov','/public/authoritative-connectors/nasa-gpm/discovery','/public/hydrology/discovery/nasa-gpm','/public/authoritative-connectors/glofas/layers','/public/hydrology/discovery/glofas'):
 assert marker in main,marker
promotion=(ROOT/'promote_site_intelligence_v4_35_13_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
print('PASS: v4.35.19 High-Priority Workspace Connector Closure III: Water, Hydrology & Sanitation release contract')
