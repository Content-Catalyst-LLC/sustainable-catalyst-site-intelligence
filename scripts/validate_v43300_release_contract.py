#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/solid-waste-circular-materials').json();cat=c.get('/public/solid-waste-circular-materials/catalog').json();st=c.get('/public/solid-waste-circular-materials/state').json();r=c.get('/public/solid-waste-circular-materials/readiness').json()
assert o.get('ok') and o.get('version')=='4.33.0' and o.get('contract')=='global-solid-waste-recycling-circular-materials-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-waste-recycling','epa-rcrainfo-hazardous-waste','world-bank-what-a-waste','eurostat-waste'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_feature_treated_as_operating_facility') is False
assert st.get('truth',{}).get('recycling_rate_treated_as_material_circularity') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.33.0 solid waste / recycling / circular-materials release contract')
