#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/agriculture-food').json();cat=c.get('/public/agriculture-food/catalog').json();st=c.get('/public/agriculture-food/state').json();r=c.get('/public/agriculture-food/readiness').json()
assert o.get('ok') and o.get('version')=='4.25.0' and o.get('source_count')==4
assert {'faostat','usda-nass-quick-stats','usda-crop-casma','geoglam-crop-monitor'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('eo_condition_treated_as_yield_measurement') is False
assert st.get('truth',{}).get('crop_monitor_condition_treated_as_platform_forecast') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.25.0 agriculture / crops / food-system conditions release contract')
