#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app);o=c.get('/public/transportation-infrastructure').json();cat=c.get('/public/transportation-infrastructure/catalog').json();st=c.get('/public/transportation-infrastructure/state').json();r=c.get('/public/transportation-infrastructure/readiness').json()
assert o.get('ok') and o.get('version')=='4.27.0' and o.get('source_count')==4 and o.get('route')=='earth'
assert {'overture-transportation','unece-unlocode','ourairports','mobilitydata-database'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('truth',{}).get('network_segment_treated_as_navigable_route') is False
assert st.get('truth',{}).get('gtfs_feed_treated_as_service_guarantee') is False
assert st.get('truth',{}).get('platform_navigation_or_safety_determination') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.27.0 transportation networks / ports / airports / transit release contract')
