#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/institutional-governance');assert s.status_code==200;s=s.json();assert s['version']=='4.15.0' and s['contract']=='institutional-workspaces-review-governance' and s['public_accounts_required'] is False and s['automatic_evidence_approval'] is False
p={'workspace_id':'workspace:bra-review','title':'Brazil review','prepared_by_role':'preparer','evidence':[{'evidence_id':'bra-pop','title':'Population','source_id':'world-bank','truth_state':'historical_only','review_state':'pending'}],'annotations':[{'target_id':'bra-pop','author_role':'reviewer','text':'Verify source period.'}]}
w=c.post('/public/institutional-governance/workspace/preview',json=p).json()['workspace'];assert len(w['workspace_sha256'])==64 and w['write_performed'] is False
q=c.post('/public/institutional-governance/review-queue',json=p).json();assert q['count']==1 and q['queue'][0]['required_role']=='reviewer'
d=c.post('/public/institutional-governance/decision/preview',json={'workspace_id':'w','target_id':'e','actor_role':'reviewer','prepared_by_role':'preparer','action':'approve_evidence'}).json()['decision'];assert d['allowed'] is True and d['automatic_transition'] is False
pack=c.post('/public/institutional-governance/package/export',json=p).json()['package'];assert len(pack['package_sha256'])==64 and pack['remote_delivery_performed'] is False
imp=c.post('/public/institutional-governance/package/import-preview',json={'package':pack}).json();assert imp['compatible'] is True and imp['automatic_import'] is False
html=(BACKEND/'public_app/index.html').read_text();worker=(BACKEND/'public_app/service-worker.js').read_text();js=(BACKEND/'public_app/assets/institutional-governance-v3300.js').read_text();assert 'institutional-governance-v3300.js?v=4.15.0' in html and 'institutional-governance-v3300.js' in worker and 'SCSIInstitutionalGovernanceV3300' in js
print(json.dumps({'version':s['version'],'workspace_sha256':w['workspace_sha256'],'review_queue':q['count'],'import_compatible':imp['compatible']},indent=2));print('PASS: Site Intelligence v4.15.0 institutional workspace and review governance contracts are complete.')
