#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/human-settlements').json();cat=c.get('/public/human-settlements/catalog').json();st=c.get('/public/human-settlements/state').json();r=c.get('/public/human-settlements/readiness').json()
assert o.get('ok') and o.get('version')=='4.26.0' and o.get('source_count')==4
assert {'jrc-ghsl','worldpop-global2','nasa-black-marble','world-bank-urban'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('population_estimate_treated_as_census_headcount') is False
assert st.get('truth',{}).get('night_lights_treated_as_electricity_service') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.26.0 human settlements / urbanization / built environment release contract')
