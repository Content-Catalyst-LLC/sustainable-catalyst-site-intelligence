from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.planetary_intelligence_v4200 import overview,catalog,readiness,state
assert overview()['version']=='4.16.0' and overview()['route']=='earth'
assert catalog()['body_count']==2 and catalog()['product_count']>=7
assert readiness()['ok'] is True
assert state('moon','lro-wac-morphology')['truth']['local_surface_texture_is_mission_imagery'] is False
assert state('mars','themis-controlled')['view']['not_earth_coordinates'] is True
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text()
assert 'data-scsi-planetary-contract="planetary-intelligence-v4200"' in html
assert '/app/assets/planetary-intelligence-v4200.js' in sw
print('PASS: v4.16.0 planetary release contract validated.')
