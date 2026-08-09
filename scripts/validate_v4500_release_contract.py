#!/usr/bin/env python3
from pathlib import Path
from fastapi.testclient import TestClient
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend')); from app.main import app
c=TestClient(app); p=c.get('/public/ocean-intelligence').json(); assert p['ok'] and p['version']=='4.11.0'; cat=c.get('/public/ocean-intelligence/catalog').json(); assert cat['source_count']>=3 and cat['variable_count']>=9; s=c.get('/public/ocean-intelligence/state',params={'variable':'sea-surface-temperature','source':'noaa-coastwatch-erddap'}).json(); assert s['condition']['value'] is None and not s['condition']['coverage_verified']; r=c.get('/public/ocean-intelligence/readiness').json(); assert r['ok']; nav=c.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6; print('PASS: v4.11.0 ocean release contract')
