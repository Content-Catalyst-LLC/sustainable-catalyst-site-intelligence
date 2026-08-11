#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
c=TestClient(app)
o=c.get('/public/seti-technosignatures').json();cat=c.get('/public/seti-technosignatures/catalog').json();st=c.get('/public/seti-technosignatures/state?target=Proxima%20Centauri&telescope=Parkes&frequency_mhz=982.002').json();r=c.get('/public/seti-technosignatures/readiness').json()
assert o.get('ok') and o.get('version')=='4.34.0' and o.get('contract')=='seti-technosignatures-radio-signal-intelligence' and o.get('route')=='earth' and o.get('source_count')==4
assert {'breakthrough-listen-open-data','breakthrough-listen-event-tables','seti-technosearch','nasa-exoplanet-target-context'}<={x.get('id') for x in cat.get('sources',[])}
assert st.get('evidence',{}).get('technosignature_confirmed') is False
assert st.get('truth',{}).get('signal_event_treated_as_technosignature') is False and st.get('truth',{}).get('non_detection_treated_as_absence') is False
assert r.get('ok') and all(r.get('checks',{}).values())
print('PASS: v4.34.0 SETI / technosignatures release contract')
