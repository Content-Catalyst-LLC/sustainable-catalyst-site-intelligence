#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/water-sanitation-infrastructure').json();cat=c.get('/public/water-sanitation-infrastructure/catalog').json();st=c.get('/public/water-sanitation-infrastructure/state').json();r=c.get('/public/water-sanitation-infrastructure/readiness').json()
assert o.get('ok') and o.get('version')=='4.32.0' and o.get('contract')=='global-water-supply-wastewater-sanitation-infrastructure-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-water-infrastructure','epa-echo-wastewater','epa-sdwis-drinking-water','who-unicef-jmp-wash'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_feature_treated_as_operating_utility') is False
assert st.get('truth',{}).get('wash_estimate_treated_as_household_service') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.32.0 water supply / wastewater / sanitation release contract')
