#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/mining-critical-materials').json();cat=c.get('/public/mining-critical-materials/catalog').json();st=c.get('/public/mining-critical-materials/state').json();r=c.get('/public/mining-critical-materials/readiness').json()
assert o.get('ok') and o.get('version')=='4.33.0' and o.get('contract')=='global-mining-mineral-resources-critical-materials-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-mining','usgs-usmin','usgs-mcs-2026','iea-critical-minerals'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_feature_treated_as_operating_mine') is False
assert st.get('truth',{}).get('scenario_gap_treated_as_shortage') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.33.0 mining / mineral resources / critical-materials release contract')
