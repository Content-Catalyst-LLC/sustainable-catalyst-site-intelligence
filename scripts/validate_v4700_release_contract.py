#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend')); from app.main import app
c=TestClient(app)
p=c.get('/public/seafloor-intelligence').json(); assert p['ok'] and p['version']=='4.17.0' and p['contract']=='seafloor-bathymetric-intelligence' and p['route']=='earth'
cat=c.get('/public/seafloor-intelligence/catalog').json(); ids={x['id'] for x in cat['sources']}; assert {'gebco-2026','emodnet-bathymetry','noaa-ncei-bathymetry'}<=ids and cat['layer_count']>=8
s=c.get('/public/seafloor-intelligence/state',params={'layer':'bathymetric-elevation','source':'gebco-2026','latitude':0,'longitude':-30}).json(); assert s['terrain']['value'] is None and not s['terrain']['point_coverage_verified'] and not s['truth']['terrain_fabricated'] and not s['truth']['grid_spacing_as_accuracy']
r=c.get('/public/seafloor-intelligence/readiness').json(); assert r['ok'] and all(r['checks'].values())
water=c.get('/public/water-column/readiness').json(); assert water['ok'] and water['version']=='4.17.0'
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.17.0 seafloor/bathymetry release contract')
