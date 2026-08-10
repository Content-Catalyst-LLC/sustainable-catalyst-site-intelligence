#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/research-integration');assert s.status_code==200;s=s.json();assert s['version']=='4.13.0' and s['contract']=='research-evidence-and-knowledge-integration' and len(s['targets'])==4 and s['human_confirmation_required'] is True and s['automatic_delivery'] is False
sample={'title':'Brazil research','question':'What does the evidence establish?','countries':['BRA'],'records':[{'id':'r1','title':'Population','record_type':'indicator','evidence_class':'official-statistic','country':'BRA','indicator_id':'SP.POP.TOTL','value':1,'unit':'people','source_id':'world-bank','source_url':'https://api.worldbank.org/','publisher':'World Bank','observed_at':'2023','retrieved_at':'2026-08-06T00:00:00Z'}]}
manifest=c.post('/public/research-integration/evidence-manifest',json=sample);assert manifest.status_code==200;manifest=manifest.json();assert manifest['record_count']==1 and len(manifest['manifest']['fingerprint'])==64
workbench=c.post('/public/research-integration/handoff/workbench/preview',json=sample).json();assert workbench['packet']['preview_only'] is True and workbench['packet']['delivery_attempted'] is False and len(workbench['packet']['payload']['datasets'])==1
library=c.post('/public/research-integration/knowledge-library/discovery',json=sample).json();assert library['plan']['match_state']=='not-executed' and library['plan']['verified_matches']==[]
html=(BACKEND/'public_app/index.html').read_text();worker=(BACKEND/'public_app/service-worker.js').read_text();js=(BACKEND/'public_app/assets/research-integration-v3270.js').read_text();assert 'research-integration-v3270.js?v=4.13.0' in html and 'research-integration-v3270.js' in worker and 'SCSIResearchIntegrationV3270' in js
policy=json.loads((BACKEND/'data/research_evidence_integration_policy_v3270.json').read_text());assert policy['version']=='4.13.0'
print(json.dumps({'version':s['version'],'targets':len(s['targets']),'manifest_fingerprint':manifest['manifest']['fingerprint'],'workbench_records':len(workbench['packet']['payload']['datasets'])},indent=2));print('PASS: Site Intelligence v4.13.0 research evidence and knowledge integration contracts are complete.')
