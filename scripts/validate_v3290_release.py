#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; BACKEND=ROOT/'backend'; sys.path.insert(0,str(BACKEND))
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
s=c.get('/public/publication-studio'); assert s.status_code==200; s=s.json(); assert s['version']=='4.12.0' and s['contract']=='briefing-story-map-publication-studio' and s['human_editorial_review_required'] is True and s['automatic_publication'] is False and s['public_write_performed'] is False
payload={'title':'Brazil intelligence brief','summary':'Reviewable public evidence.','methodology':['Preserve source identity and dates.'],'limitations':['Does not establish causation.'],'frozen_at':'2026-08-07T00:00:00Z','sources':[{'source_id':'world-bank','publisher':'World Bank','source_url':'https://data.worldbank.org','truth_state':'historical_only'}],'evidence':[{'evidence_id':'bra-pop','source_id':'world-bank','country':'BRA','indicator_id':'SP.POP.TOTL','value':216422446,'unit':'people','observed_at':'2023','truth_state':'historical_only'}],'blocks':[{'block_type':'map','title':'Brazil','text':'Selected geography','source_ids':['world-bank'],'evidence_ids':['bra-pop'],'alt_text':'Map showing Brazil.'}]}
manifest=c.post('/public/publication-studio/frozen-manifest',json=payload).json()['manifest']; assert manifest['source_count']==1 and manifest['evidence_count']==1 and len(manifest['manifest_sha256'])==64 and manifest['proof_of_accuracy'] is False
brief=c.post('/public/publication-studio/briefing/preview',json=payload).json()['brief']; assert brief['editorial_state']=='draft' and brief['human_review_required'] is True and brief['write_performed'] is False
story=c.post('/public/publication-studio/story-map/preview',json=payload).json()['story_map']; assert story['accessibility']['status']=='pass' and story['automatic_publication'] is False
ready=c.post('/public/publication-studio/readiness',json=payload).json(); assert ready['status']=='ready-for-human-review' and ready['publish_allowed'] is False
package=c.post('/public/publication-studio/package',json=payload).json(); assert package['packet']['print_html_ready'] is True and package['packet']['pdf_binary_generated'] is False and package['packet']['human_review_required'] is True
correction=c.post('/public/publication-studio/correction/preview',json={'publication_id':'brief:bra','version_id':'brief:bra:v1','action':'correction','note':'Correct observation period.'}).json()['correction']; assert correction['preserves_prior_version'] is True and correction['write_performed'] is False
html=(BACKEND/'public_app/index.html').read_text(); worker=(BACKEND/'public_app/service-worker.js').read_text(); js=(BACKEND/'public_app/assets/briefing-publication-v3290.js').read_text(); assert 'briefing-publication-v3290.js?v=4.12.0' in html and 'briefing-publication-v3290.js' in worker and 'SCSIBriefingPublicationV3290' in js
policy=json.loads((BACKEND/'data/briefing_publication_policy_v3290.json').read_text()); assert policy['version']=='4.12.0' and 'retraction' in policy['correction_actions']
print(json.dumps({'version':s['version'],'manifest_sha256':manifest['manifest_sha256'],'readiness':ready['status'],'story_accessibility':story['accessibility']['status'],'correction_preserves_prior_version':correction['preserves_prior_version']},indent=2)); print('PASS: Site Intelligence v4.12.0 Briefing, Story Map, and Publication Studio contracts are complete.')
