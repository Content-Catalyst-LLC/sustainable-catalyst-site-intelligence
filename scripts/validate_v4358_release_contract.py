#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.workspace_evidence_unification_v4358 import canonicalize_country_indicator, overview, readiness
from app.release_health_v43531 import deployment_verification, source_health_policy
assert APP_VERSION=='4.35.9'
settings=Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')
assert overview()['contract']=='workspace-evidence-unification-truth-layer'
assert readiness()['ok'] is True and readiness()['network_calls_performed'] is False
obs=canonicalize_country_indicator(
    {'code':'PSE','iso2':'PS','name':'Palestine'},
    {'id':'EG.ELC.ACCS.ZS','key':'electricity_access','label':'Access to electricity','domain':'Infrastructure','format':'percent','unit':'% of population','latest':{'year':2024,'value':100.0},'source':'World Bank Open Data','source_url':'https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS?locations=PS','data_state':'live','cache_state':'live','retrieved_at':'2026-08-11T05:00:00+00:00','stale':False,'lineage':{}},
)
assert obs['value']['number']==100.0 and obs['semantics']['concept_id']=='electricity_structural_access'
assert 'current electricity availability' in obs['semantics']['forbidden_substitutions']
assert len(obs['fingerprint']['value'])==64
missing=canonicalize_country_indicator(
    {'code':'PSE','iso2':'PS','name':'Palestine'},
    {'id':'EG.ELC.ACCS.ZS','key':'electricity_access','label':'Access to electricity','domain':'Infrastructure','format':'percent','unit':'% of population','latest':None,'source':'World Bank Open Data','source_url':'https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS?locations=PS','data_state':'unavailable','cache_state':'unavailable','retrieved_at':None,'stale':False,'lineage':{}},
)
assert missing['truth_state']=='missing' and missing['value']['available'] is False
verify=deployment_verification(settings); assert verify['ok'] and verify['version']==APP_VERSION and verify['source_health_blocks_release'] is False
policy=source_health_policy(settings); assert policy['ok'] and policy['summary']['release_blocking_sources']==0
client=TestClient(app)
for endpoint in ('/public/workspace-evidence','/public/workspace-evidence/readiness','/public/evidence-intelligence','/public/evidence-intelligence/readiness','/public/deployment-verification','/public/source-health-policy'):
    response=client.get(endpoint); assert response.status_code==200,endpoint
main=(ROOT/'backend/app/main.py').read_text()
assert 'workspace_evidence_unification_v4358' in main and 'record_provenance_v4358' in main
for endpoint in ('/public/workspace-evidence','/public/workspace-evidence/readiness','/public/workspace-evidence/country/{country_code}','/public/workspace-evidence/country/{country_code}/indicator/{indicator_id}'):
    assert endpoint in main,endpoint
app_js=(ROOT/'backend/public_app/assets/app.js').read_text()
truth_js=(ROOT/'backend/public_app/assets/record-provenance-v3238.js').read_text()
assert 'data-canonical-observation' in app_js and 'data-record-truth-indicator' in app_js
assert 'Canonical observation' in truth_js and 'Canonical SHA-256' in truth_js
promotion=(ROOT/'promote_site_intelligence_v4_35_8_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion and '/public/workspace-evidence/readiness' in promotion
print('PASS: v4.35.9 workspace evidence unification & truth-layer repair release contract')
