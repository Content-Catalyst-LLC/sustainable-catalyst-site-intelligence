#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/monitoring-operations');assert s.status_code==200;s=s.json();assert s['version']=='4.16.0' and s['contract']=='monitoring-digests-and-early-warning-operations' and len(s['alert_states'])==5 and len(s['watch_types'])==4 and s['human_review_required'] is True and s['automatic_publication'] is False and s['automatic_emergency_dispatch'] is False
watch={'title':'Brazil energy watch','countries':['BRA'],'areas':[{'id':'bra','label':'Brazil','country':'BRA'}],'rules':[{'id':'r1','name':'Energy threshold','indicator_id':'energy-use','country':'BRA','source_id':'world-bank','operator':'>=','threshold':10,'unit':'GJ/person'}]}
signal={'id':'bra-energy','title':'Energy use','indicator_id':'energy-use','country':'BRA','source_id':'world-bank','value':10.5,'unit':'GJ/person','observed_at':'2023','retrieved_at':'2026-08-06T00:00:00Z','freshness':'historical_only'}
evalp=c.post('/public/monitoring-operations/evaluate',json={'watchlist':watch,'signals':[signal]});assert evalp.status_code==200;evalp=evalp.json();assert evalp['alert_count']==1 and evalp['alerts'][0]['state']=='new' and evalp['alerts'][0]['operational_emergency_alert'] is False
digest=c.post('/public/monitoring-operations/digest/preview',json={'title':'Brazil monitoring','alerts':evalp['alerts']}).json();assert digest['digest']['status']=='draft' and digest['digest']['publication_allowed'] is False and digest['digest']['human_review_required'] is True
warning=c.post('/public/monitoring-operations/modeled-warning/preview',json={'model_id':'demo','model_output':0.8,'threshold':0.7}).json();assert warning['warning']['modeled_warning'] is True and warning['warning']['source_alert'] is False and warning['warning']['automatic_action'] is False
source=c.post('/public/monitoring-operations/source-changes',json={'previous':[{'source_id':'world-bank','schema_fingerprint':'a','status':'operational'}],'current':[{'source_id':'world-bank','schema_fingerprint':'b','status':'degraded'}]}).json();assert source['change_count']==1 and source['publisher_wide_outage_claimed'] is False
feed=c.get('/public/monitoring-operations/feed-contract').json();assert feed['published_items_must_be_human_approved'] is True and feed['subscriber_profile_required'] is False
html=(BACKEND/'public_app/index.html').read_text();worker=(BACKEND/'public_app/service-worker.js').read_text();js=(BACKEND/'public_app/assets/monitoring-operations-v3280.js').read_text();assert 'monitoring-operations-v3280.js?v=4.16.0' in html and 'monitoring-operations-v3280.js' in worker and 'SCSIMonitoringOperationsV3280' in js
policy=json.loads((BACKEND/'data/monitoring_early_warning_policy_v3280.json').read_text());assert policy['version']=='4.16.0' and policy['prohibited']['automatic_publication'] is True
print(json.dumps({'version':s['version'],'alert_states':len(s['alert_states']),'watch_types':len(s['watch_types']),'sample_alert_state':evalp['alerts'][0]['state'],'digest_status':digest['digest']['status']},indent=2));print('PASS: Site Intelligence v4.16.0 Monitoring, Digests, and Early-Warning Operations contracts are complete.')
