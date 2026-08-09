#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/assurance');assert s.status_code==200;s=s.json();assert s['version']=='4.3.0' and s['contract']=='comparative-scenario-model-assurance' and len(s['comparison_dimensions'])>=6
scenario=c.post('/public/assurance/scenario',json={'baseline':100,'assumptions':[{'id':'a','mode':'percent','low':-5,'base':10,'high':20}]});assert scenario.status_code==200;scenario=scenario.json();assert scenario['base_outcome']==110 and scenario['uncertainty_envelope']['probabilistic'] is False
cards=c.get('/public/assurance/model-cards').json();assert cards['method_card_count']>=2
html=(BACKEND/'public_app/index.html').read_text();worker=(BACKEND/'public_app/service-worker.js').read_text();js=(BACKEND/'public_app/assets/assurance-v3260.js').read_text();assert 'assurance-v3260.js?v=4.3.0' in html and 'assurance-v3260.js' in worker and 'SCSIAssuranceV3260' in js
policy=json.loads((BACKEND/'data/comparative_model_assurance_policy_v3260.json').read_text());assert policy['version']=='4.3.0'
print(json.dumps({'version':s['version'],'dimensions':len(s['comparison_dimensions']),'method_cards':cards['method_card_count'],'scenario_fingerprint':scenario['fingerprint']},indent=2));print('PASS: Site Intelligence v4.3.0 comparative, scenario, and model assurance contracts are complete.')
