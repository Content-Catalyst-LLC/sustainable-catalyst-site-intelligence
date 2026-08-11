#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.evidence_intelligence_v4357 import overview, metric_catalog, precedence_catalog, freshness_assessment, select_evidence, readiness
from app.authoritative_api_audit_v4357 import audit_overview, audit_readiness
from app.authoritative_connectors_v4356 import connector_catalog
from app.release_health_v43531 import deployment_verification, source_health_policy
assert APP_VERSION=='4.35.7'
settings=Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')
assert overview()['metric_concept_count'] >= 9
assert readiness()['ok'] is True and readiness()['network_calls_performed'] is False
assert metric_catalog()['indicator_mapping']['EG.ELC.ACCS.ZS']=='electricity_structural_access'
rules=precedence_catalog(jurisdiction='PSE',concept_id='electricity_structural_access')['rules']
assert rules and rules[0]['preferred_sources'][0]=='pcbs-pxweb-sdgs'
ops=precedence_catalog(jurisdiction='PSE',concept_id='electricity_operational_availability')['rules']
assert ops and 'world_bank' not in ops[0]['preferred_sources']
assert freshness_assessment(observed_at='2025-12-31',cadence='annual',now='2026-08-11')['status'] in {'current','recent'}
assert freshness_assessment(observed_at='2025-12-31',cadence='near_real_time',now='2026-08-11')['status']=='stale'
selection=select_evidence(concept_id='electricity_operational_availability',jurisdiction='PSE',candidates=[{'source_id':'world_bank','indicator_id':'EG.ELC.ACCS.ZS','value':100.0,'unit':'% of population'}])
assert selection['selected'] is None and selection['selection_state']=='no-semantically-eligible-evidence'
verify=deployment_verification(settings); assert verify['ok'] and verify['version']==APP_VERSION and verify['source_health_blocks_release'] is False
policy=source_health_policy(settings); assert policy['ok'] and policy['summary']['release_blocking_sources']==0
catalog=connector_catalog(settings); assert catalog['connector_count']==20
api_audit=audit_overview(settings); assert api_audit['summary']['source_registrations']==184 and api_audit['evidence_intelligence']['version']==APP_VERSION
assert audit_readiness(settings)['ok'] is True
client=TestClient(app)
for endpoint in ('/public/evidence-intelligence','/public/evidence-intelligence/metrics','/public/evidence-intelligence/precedence?jurisdiction=PSE&concept_id=electricity_structural_access','/public/evidence-intelligence/freshness?observed_at=2024-12-31&cadence=annual','/public/evidence-intelligence/indicator/EG.ELC.ACCS.ZS?jurisdiction=PSE','/public/evidence-intelligence/readiness','/public/authoritative-apis','/public/deployment-verification','/public/source-health-policy'):
    response=client.get(endpoint); assert response.status_code==200,endpoint
record=client.get('/public/record-truth/indicator/PSE/EG.ELC.ACCS.ZS'); assert record.status_code==200
body=record.json(); assert body['semantics']['concept_id']=='electricity_structural_access' and 'current electricity availability' in body['semantics']['forbidden_substitutions']
main=(ROOT/'backend/app/main.py').read_text(); assert 'authoritative_api_audit_v4357' in main and 'record_provenance_v4357' in main
for endpoint in ('/public/evidence-intelligence','/public/evidence-intelligence/select','/public/evidence-intelligence/readiness'): assert endpoint in main
promotion=(ROOT/'promote_site_intelligence_v4_35_7_to_github_and_render_macos.sh').read_text(); assert 'Deep gate:' not in promotion and '/public/deployment-verification' in promotion and '/public/source-health-policy' in promotion
print('PASS: v4.35.7 source precedence, metric semantics & freshness intelligence release contract')
