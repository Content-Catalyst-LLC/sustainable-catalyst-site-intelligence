#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
p=c.get('/public/ocean-missions').json(); assert p['ok'] and p['version']=='4.13.0' and p['contract']=='ocean-missions-vehicles-observatory-network' and p['route']=='earth' and p['source_count']==4 and p['platform_type_count']>=10
cat=c.get('/public/ocean-missions/catalog').json(); ids={x['id'] for x in cat['sources']}; assert ids=={'argo','ioos','onc','noaa-ocean-exploration'}
s=c.get('/public/ocean-missions/state',params={'source':'argo','platform_type':'float','platform_id':'5901234','latitude':35.1,'longitude':-145.2}).json(); assert s['evidence']['platform_record_loaded'] is False and s['truth']['current_position_verified'] is False and s['truth']['continuous_trajectory_verified'] is False and s['truth']['future_trajectory_predicted'] is False
r=c.get('/public/ocean-missions/readiness').json(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
bio=c.get('/public/marine-biodiversity/readiness').json(); assert bio['ok'] and bio['version']=='4.13.0'
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.13.0 ocean missions / vehicles / observatory release contract')
