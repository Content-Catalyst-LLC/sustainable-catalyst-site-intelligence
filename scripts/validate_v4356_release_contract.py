#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.release_health_v43531 import deployment_verification, source_health_policy
from app.version import APP_VERSION
from app.authoritative_connectors_v4356 import connector_catalog, connector_readiness
from app.authoritative_api_audit_v4356 import audit_overview
assert APP_VERSION=='4.35.20'
settings=Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')
verify=deployment_verification(settings)
assert verify['ok'] and verify['version']==APP_VERSION and verify['source_health_blocks_release'] is False
assert verify['network_calls_performed'] is False and all(verify['checks'].values())
catalog=connector_catalog(settings)
assert catalog['connector_count']==20
assert catalog['live_connector_count']==16 and catalog['discovery_connector_count']==2
assert catalog['auth_required_connector_count']==2 and catalog['configured_auth_required_connector_count']==0
assert connector_readiness(settings)['ok'] is True
audit=audit_overview(settings); summary=audit['summary']
assert len(audit['completed_connector_targets'])==20
assert summary['source_registrations']==184 and summary['machine_readable_registrations']==101
assert summary['implemented_or_configuration_gated_registrations']==66
assert summary['counts']['LIVE']==46 and summary['counts']['DISCOVERY']==8
assert summary['counts']['AUTH_REQUIRED']==12 and summary['counts']['BULK']==4 and summary['counts']['STALE']==0
assert summary['registered_but_not_retrieved']==45
policy=source_health_policy(settings)
assert policy['ok'] and policy['summary']['release_blocking_sources']==0 and policy['network_calls_performed'] is False
client=TestClient(app)
for endpoint in ('/health','/public/runtime-health','/public/v4/readiness','/public/authoritative-connectors/readiness','/public/deployment-verification','/public/source-health-policy','/public/authoritative-connectors'):
    r=client.get(endpoint); assert r.status_code==200,endpoint
assert client.get('/public/v4/readiness').json()['summary']['preserved_routes']==35
main=(ROOT/'backend/app/main.py').read_text()
for endpoint in ('/public/authoritative-connectors/pcbs/pxweb/metadata','/public/authoritative-connectors/pcbs/pxweb/data','/public/authoritative-connectors/statcan/vectors','/public/authoritative-connectors/ons/observations','/public/authoritative-connectors/abs/sdmx','/public/authoritative-connectors/bls/timeseries'):
    assert endpoint in main
promotion=(ROOT/'promote_site_intelligence_v4_35_6_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion and '/public/deployment-verification' in promotion and '/public/source-health-policy' in promotion
assert '/public/climate/state' not in promotion and 'External source availability is intentionally excluded' in promotion
render=(ROOT/'render.yaml').read_text()
for marker in ('site-intelligence-v4.35.20','SC_SI_NASA_FIRMS_MAP_KEY','SC_SI_USDA_NASS_API_KEY','SC_SI_NASA_EARTHDATA_TOKEN'):
    assert marker in render
print('PASS: v4.35.20 national statistical & domain-authority connector expansion release contract')
