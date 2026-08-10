#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/wetlands-inland-water').json();cat=c.get('/public/wetlands-inland-water/catalog').json();st=c.get('/public/wetlands-inland-water/state').json();r=c.get('/public/wetlands-inland-water/readiness').json()
assert o.get('ok') and o.get('version')=='4.24.0' and o.get('source_count')==4
assert {'usfws-nwi','ramsar-rsis','jrc-global-surface-water','nasa-swot-inland-water'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_wetland_treated_as_jurisdictional_wetland') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.24.0 wetlands / inland waters / aquatic habitat release contract')
