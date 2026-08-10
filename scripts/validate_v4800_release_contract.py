#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
p=c.get('/public/underwater-observation').json(); assert p['ok'] and p['version']=='4.15.0' and p['contract']=='underwater-observation-visual-evidence' and p['route']=='earth' and p['source_count']==3 and p['media_type_count']==4
cat=c.get('/public/underwater-observation/catalog').json(); ids={x['id'] for x in cat['sources']}; assert ids=={'onc-oceans-3','fathomnet','noaa-ocean-exploration'}
s=c.get('/public/underwater-observation/state',params={'source':'fathomnet','media_type':'still-image','latitude':36.7,'longitude':-122,'depth_m':1200,'query':'Octopus'}).json(); assert s['media']['record_loaded'] is False and s['media']['media_url'] is None and not s['truth']['visual_media_fabricated'] and not s['truth']['model_inference_as_verified_observation']
r=c.get('/public/underwater-observation/readiness').json(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
sea=c.get('/public/seafloor-intelligence/readiness').json(); assert sea['ok'] and sea['version']=='4.15.0'
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.15.0 underwater observation / visual evidence release contract')
