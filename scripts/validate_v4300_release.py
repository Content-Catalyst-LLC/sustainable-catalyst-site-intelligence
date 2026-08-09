#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.astronomical_observation_v4300 import overview,catalog,state,readiness
from app.unified_public_intelligence_v4000 import public_unified_navigation
o=overview();c=catalog();s=state('m31','wise-mid-ir',field_deg=.25);r=readiness();nav=public_unified_navigation()
assert o['ok'] and o['version']=='4.4.0' and o['route']=='earth'
assert c['survey_count']>=7 and c['target_count']>=6
assert s['truth']['local_orientation_is_survey_imagery'] is False and s['truth']['live_telescope_feed_claimed'] is False
assert r['ok'] and all(r['checks'].values())
assert nav['route_count']==35 and nav['primary_area_count']==6
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text(); js=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text(); css=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.css').read_text()
assert 'data-scsi-release="4.4.0"' in html and 'data-scsi-astronomical-contract="astronomical-observation-v4300"' in html
assert 'astronomical-observation-v4300.js?v=4.4.0' in html and 'astronomical-observation-v4300.css?v=4.4.0' in html
assert 'astronomical-observation-v4300.js' in sw and 'astronomical-observation-v4300.css' in sw
assert 'SCSIAstronomicalV4300' in js and '.astro4300-stage' in css
assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/astronomical-observation-v4300.js').read_text()
assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/astronomical-observation-v4300.css').read_text()
print(json.dumps({'version':'4.4.0','contract':o['contract'],'surveys':c['survey_count'],'targets':c['target_count'],'routes':nav['route_count'],'primary_areas':nav['primary_area_count'],'readiness':r['ok'],'state_sha256':s['state_sha256']},indent=2))
print('PASS: Site Intelligence v4.4.0 Astronomical Observation Environment contracts are complete.')
