#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
p=c.get('/public/marine-biodiversity').json(); assert p['ok'] and p['version']=='4.16.0' and p['contract']=='marine-biodiversity-bioacoustic-intelligence' and p['route']=='earth' and p['source_count']==4 and p['evidence_class_count']==6
cat=c.get('/public/marine-biodiversity/catalog').json(); ids={x['id'] for x in cat['sources']}; assert ids=={'obis','worms','fathomnet','onc-hydrophones'}
s=c.get('/public/marine-biodiversity/state',params={'source':'onc-hydrophones','evidence_class':'acoustic-detection','scientific_name':'Orcinus orca','latitude':48.5,'longitude':-126.2,'depth_m':900}).json(); assert s['evidence']['records_loaded'] is False and s['evidence']['presence_verified'] is False and s['evidence']['absence_verified'] is False and s['truth']['model_detection_as_verified_species'] is False and s['truth']['zero_results_as_absence'] is False
r=c.get('/public/marine-biodiversity/readiness').json(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
uw=c.get('/public/underwater-observation/readiness').json(); assert uw['ok'] and uw['version']=='4.16.0'
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.16.0 marine biodiversity / bioacoustic release contract')
