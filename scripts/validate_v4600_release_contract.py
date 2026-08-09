#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend')); from app.main import app
c=TestClient(app)
p=c.get('/public/water-column').json(); assert p['ok'] and p['version']=='4.11.0' and p['contract']=='water-column-depth-explorer'
cat=c.get('/public/water-column/catalog').json(); assert cat['source_count']>=3 and cat['variable_count']>=8 and cat['maximum_navigation_depth_m']==11000
s=c.get('/public/water-column/state',params={'variable':'temperature','source':'argo-argovis','depth_m':1000}).json(); assert s['condition']['value'] is None and not s['condition']['depth_sample_verified'] and not s['truth']['depth_value_interpolated']
r=c.get('/public/water-column/readiness').json(); assert r['ok'] and r['checks']['no_automatic_interpolation'] and r['checks']['nearest_sample_not_substituted']
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.11.0 water-column release contract')
