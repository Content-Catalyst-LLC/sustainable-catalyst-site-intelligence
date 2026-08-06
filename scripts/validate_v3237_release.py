#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION
assert APP_VERSION=='3.23.7'
client=TestClient(app)
countries=client.get('/public/data-truth/countries').json();assert countries['country_count']>=170
for code in ('KEN','GHA','USA','IND','BRA','DEU'):
 payload=client.get(f'/public/data-truth/country/{code}').json();assert payload['ok'] and payload['country']['code']==code and payload['source_count']==8
matrix=client.get('/public/data-truth/coverage-matrix?countries=KEN,GHA,USA,IND,BRA,DEU').json();assert matrix['country_count']==6 and matrix['source_count']==8
html=(ROOT/'backend/public_app/index.html').read_text();worker=(ROOT/'backend/public_app/service-worker.js').read_text();php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
for token in ('data-truth-v3237.css?v=3.23.7','data-truth-v3237.js?v=3.23.7'):assert token in html
assert 'data-truth-v3237.js' in worker and 'Version: 3.23.7' in php
print('Site Intelligence v3.23.7 global country data truth release contract passed.')
