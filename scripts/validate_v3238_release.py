#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION
from app.record_provenance_v3238 import MAP_LAYERS
assert APP_VERSION=='4.5.0'
client=TestClient(app)
indicator=client.get('/public/record-truth/indicator/KEN/SP.POP.TOTL').json()
assert indicator['ok'] and indicator['version']=='4.5.0'
assert indicator['record_id']=='indicator:KEN:SP.POP.TOTL'
assert indicator['truth_state']=='historical_snapshot'
assert indicator['dates']['observation_year']==2023
assert indicator['units']['original']=='people'
assert len(indicator['fingerprint']['value'])==64
missing=client.get('/public/record-truth/indicator/BRA/SP.POP.TOTL').json()
assert missing['truth_state']=='missing' and missing['value']['available'] is False
layer=client.get('/public/record-truth/map-layer/true-color?date=2026-08-05').json()
assert layer['truth_state']=='context_only' and layer['dates']['observation_at']=='2026-08-05'
normalized=client.post('/public/record-truth/resolve',json={'record_type':'event','id':'validator-event','title':'Validator event','source':'USGS','source_url':'https://earthquake.usgs.gov/','observed_at':'2026-08-05T00:00:00Z','country_code':'USA','data_state':'live'}).json()
assert normalized['record_id']=='event:validator-event' and normalized['truth_state']=='observed'
manifest=client.get('/public/record-truth/manifest?country=KEN').json()
assert manifest['entry_count']==8+len(MAP_LAYERS) and len(manifest['manifest_fingerprint'])==64
assert all(len(row['fingerprint'])==64 for row in manifest['entries'])
# Existing global country truth remains intact.
countries=client.get('/public/data-truth/countries').json(); assert countries['country_count']>=170
html=(ROOT/'backend/public_app/index.html').read_text(); worker=(ROOT/'backend/public_app/service-worker.js').read_text()
record_js=(ROOT/'backend/public_app/assets/record-provenance-v3238.js').read_text(); app_js=(ROOT/'backend/public_app/assets/app.js').read_text()
php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
for token in ('record-provenance-v3238.css?v=4.5.0','record-provenance-v3238.js?v=4.5.0','mapLayerTruthButton'): assert token in html
assert 'record-provenance-v3238.js' in worker and 'record-provenance-v3238.css' in worker
assert 'SCSIRecordProvenanceV3238' in record_js and '/public/record-truth/manifest' in record_js
assert 'data-record-truth-indicator' in app_js and 'scsi:record-truth' in app_js
assert 'Version: 4.5.0' in php
assert (ROOT/'backend/public_app/assets/record-provenance-v3238.js').read_bytes()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/record-provenance-v3238.js').read_bytes()
print('Site Intelligence v4.5.0 record provenance and indicator truth release contract passed.')
