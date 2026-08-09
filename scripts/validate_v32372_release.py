#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION
assert APP_VERSION=='4.6.0'
client=TestClient(app)
countries=client.get('/public/data-truth/countries').json();assert countries['country_count']>=170
for code in ('KEN','GHA','USA','IND','BRA','DEU'):
 payload=client.get(f'/public/data-truth/country/{code}').json();assert payload['ok'] and payload['country']['code']==code and payload['source_count']==8
matrix=client.get('/public/data-truth/coverage-matrix?countries=KEN,GHA,USA,IND,BRA,DEU').json();assert matrix['country_count']==6 and matrix['source_count']==8
html=(ROOT/'backend/public_app/index.html').read_text();worker=(ROOT/'backend/public_app/service-worker.js').read_text();app_js=(ROOT/'backend/public_app/assets/app.js').read_text();truth_js=(ROOT/'backend/public_app/assets/data-truth-v32371.js').read_text();reliability=(ROOT/'backend/public_app/assets/browser-reliability-v3235.js').read_text();css=(ROOT/'backend/public_app/assets/app.css').read_text();php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
for token in ('data-truth-v32371.css?v=4.6.0','data-truth-v32371.js?v=4.6.0'):assert token in html
assert 'data-truth-v32371.js' in worker and 'Version: 4.6.0' in php
assert 'const countryCatalogTask=hydrateCountrySelector(initialCountry)' in app_js
assert '/public/data-truth/countries' in app_js and 'scsi:country-catalog-ready' in app_js
assert 'scsi:country-catalog-ready' in truth_js and 'SCSIDataTruthV32371' in truth_js
assert 'function userControlFocused()' in reliability
assert "if(!next||next===lastRoute)return" in reliability
assert 'if(userControlFocused())return' in reliability
assert 'scsi:route-transition-end' in reliability
assert '#countrySelect{touch-action:auto;overscroll-behavior:auto;scroll-behavior:auto}' in css
contract=client.get('/public/browser-reliability').json();assert contract['accessibility']['form_control_focus_protection'] and contract['accessibility']['native_select_scroll_preserved'] and contract['accessibility']['route_focus_only_on_route_change']
print('Site Intelligence v4.6.0 country dropdown interaction and focus-safety release contract passed.')
