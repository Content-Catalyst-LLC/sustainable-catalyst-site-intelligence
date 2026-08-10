#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/energy-systems').json();cat=c.get('/public/energy-systems/catalog').json();st=c.get('/public/energy-systems/state').json();r=c.get('/public/energy-systems/readiness').json()
assert o.get('ok') and o.get('version')=='4.28.0' and o.get('contract')=='global-energy-infrastructure-power-systems-electricity-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-power','eia-open-data','ember-electricity-data','entsoe-transparency'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_power_feature_treated_as_energized_asset') is False
assert st.get('truth',{}).get('forecast_treated_as_observation') is False
assert st.get('truth',{}).get('platform_grid_reliability_or_safety_determination') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.28.0 energy infrastructure / power systems / electricity release contract')
