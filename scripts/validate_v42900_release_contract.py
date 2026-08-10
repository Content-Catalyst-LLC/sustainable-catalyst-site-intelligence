#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/digital-connectivity').json();cat=c.get('/public/digital-connectivity/catalog').json();st=c.get('/public/digital-connectivity/state').json();r=c.get('/public/digital-connectivity/readiness').json()
assert o.get('ok') and o.get('version')=='4.29.0' and o.get('contract')=='global-digital-connectivity-broadband-internet-performance-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'openstreetmap-telecom','mlab-network-performance','world-bank-connectivity','fcc-broadband-data'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('mapped_feature_treated_as_coverage_or_operating_asset') is False
assert st.get('truth',{}).get('performance_sample_treated_as_universal_local_performance') is False
assert st.get('truth',{}).get('platform_outage_or_coverage_determination') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.29.0 digital connectivity / broadband / internet performance release contract')
