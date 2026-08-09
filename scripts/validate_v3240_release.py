#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION

assert APP_VERSION == '4.7.0'
client = TestClient(app)

overview = client.get('/public/data-truth/control-plane').json()
assert overview['ok'] and overview['version'] == '4.7.0'
assert overview['contract'] == 'global-data-truth-control-plane'
assert overview['source_count'] == 8
assert len(overview['control_plane_fingerprint']) == 64
assert sum(overview['summary'][state] for state in ('operational','degraded','review','unavailable','unknown')) == 8
assert all(len(row['status_fingerprint']) == 64 for row in overview['sources'])

source = client.get('/public/data-truth/control-plane/source/world_bank').json()
assert source['source']['feed_id'] == 'world_bank'
assert len(source['country_examples']) == 3
assert client.get('/public/data-truth/control-plane/source/not-a-source').status_code == 404

history = client.get('/public/data-truth/control-plane/history?source=world_bank').json()
assert history['complete_event_log'] is False and history['event_count'] >= 1
schema = client.get('/public/data-truth/control-plane/schema-drift').json()
assert schema['source_count'] == 8
outages = client.get('/public/data-truth/control-plane/outages').json()
assert outages['incident_count'] == len(outages['incidents'])
coverage = client.get('/public/data-truth/control-plane/coverage?countries=KEN,BRA,USA').json()
assert coverage['country_count'] == 3 and coverage['source_count'] == 8
assert sum(coverage['state_counts'].values()) == 24
workspaces = client.get('/public/data-truth/control-plane/workspaces?country=BRA').json()
assert workspaces['country']['code'] == 'BRA' and workspaces['workspace_count'] == 12
export = client.get('/public/data-truth/control-plane/export?countries=KEN,BRA&country=BRA').json()
assert export['contract'] == 'global-data-truth-control-plane-export'
assert len(export['export_fingerprint']) == 64
assert set(export['payload']) == {'overview','schema_drift','outages','coverage','workspaces'}

# Inherited country and record truth contracts remain available.
assert client.get('/public/data-truth/countries').json()['country_count'] >= 170
assert client.get('/public/record-truth/indicator/KEN/SP.POP.TOTL').json()['truth_state'] == 'historical_snapshot'
assert client.get('/public/record-truth/indicator/BRA/SP.POP.TOTL').json()['truth_state'] == 'missing'

html = (ROOT / 'backend/public_app/index.html').read_text()
worker = (ROOT / 'backend/public_app/service-worker.js').read_text()
truth_js = (ROOT / 'backend/public_app/assets/data-truth-v32371.js').read_text()
control_js = (ROOT / 'backend/public_app/assets/data-truth-control-plane-v3240.js').read_text()
php = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
for token in ('data-truth-control-plane-v3240.css?v=4.7.0','data-truth-control-plane-v3240.js?v=4.7.0'):
    assert token in html
assert 'data-truth-control-plane-v3240.js' in worker and 'data-truth-control-plane-v3240.css' in worker
assert 'data-truth-view="control"' in truth_js and 'loadControl' in truth_js
assert 'SCSIDataTruthControlPlaneV3240' in control_js
for endpoint in ('/public/data-truth/control-plane','/public/data-truth/control-plane/schema-drift','/public/data-truth/control-plane/outages','/public/data-truth/control-plane/workspaces','/public/data-truth/control-plane/export'):
    assert endpoint in control_js or endpoint in (ROOT / 'backend/app/main.py').read_text()
assert 'Version: 4.7.0' in php
for name in ('data-truth-control-plane-v3240.js','data-truth-control-plane-v3240.css','data-truth-v32371.js'):
    assert (ROOT / 'backend/public_app/assets' / name).read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets' / name).read_bytes()
print('Site Intelligence v4.7.0 Global Data Truth Control Plane release contract passed.')
