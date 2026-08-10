#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
p=c.get('/public/ocean-events').json(); assert p['ok'] and p['version']=='4.15.0' and p['contract']=='ocean-events-hazards-ecosystem-change' and p['route']=='earth' and p['source_count']==4 and p['hazard_type_count']>=8
cat=c.get('/public/ocean-events/catalog').json(); ids={x['id'] for x in cat['sources']}; assert ids=={'noaa-coral-reef-watch','noaa-coastwatch','copernicus-marine','noaa-nccos'}
s=c.get('/public/ocean-events/state',params={'source':'noaa-nccos','hazard_type':'harmful-algal-bloom','latitude':27.8,'longitude':-82.6}).json(); assert s['evidence']['condition_record_loaded'] is False and s['truth']['hazard_declared'] is False and s['truth']['warning_issued_by_platform'] is False and s['truth']['zero_records_treated_as_safe'] is False
r=c.get('/public/ocean-events/readiness').json(); assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
missions=c.get('/public/ocean-missions/readiness').json(); assert missions['ok'] and missions['version']=='4.15.0'
nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6
print('PASS: v4.15.0 ocean events / hazards / ecosystem change release contract')
