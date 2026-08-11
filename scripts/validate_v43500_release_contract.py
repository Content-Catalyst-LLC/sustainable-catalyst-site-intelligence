#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
o=c.get('/public/exoplanet-habitability').json();cat=c.get('/public/exoplanet-habitability/catalog').json();st=c.get('/public/exoplanet-habitability/state?target=TRAPPIST-1%20e').json();r=c.get('/public/exoplanet-habitability/readiness').json()
assert o.get('ok') and o.get('version')=='4.35.1' and o.get('contract')=='exoplanets-habitability-atmospheric-biosignature-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'nasa-exoplanet-archive-systems','nasa-exoplanet-archive-atmospheres','exo-mast','mast-jwst-spectraldb'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('evidence',{}).get('life_confirmed') is False
assert st.get('truth',{}).get('habitable_zone_treated_as_habitability') is False and st.get('truth',{}).get('biosignature_treated_as_life_detection') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.35.1 exoplanets / habitability / atmospheric biosignature release contract')
