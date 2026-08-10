#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/industrial-manufacturing').json();cat=c.get('/public/industrial-manufacturing/catalog').json();st=c.get('/public/industrial-manufacturing/state').json();r=c.get('/public/industrial-manufacturing/readiness').json()
assert o.get('ok') and o.get('version')=='4.30.0' and o.get('contract')=='global-industrial-facilities-manufacturing-trade-flow-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-industrial','world-bank-manufacturing','world-bank-gem','world-bank-wits-trade'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_feature_treated_as_operating_facility') is False
assert st.get('truth',{}).get('bilateral_trade_treated_as_supply_chain_dependency') is False
assert st.get('truth',{}).get('platform_disruption_or_shortage_determination') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.30.0 industrial facilities / manufacturing / trade-flow release contract')
