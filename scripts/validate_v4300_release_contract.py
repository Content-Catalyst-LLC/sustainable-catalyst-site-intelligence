from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.astronomical_observation_v4300 import overview,catalog,readiness,state
assert overview()['version']=='4.12.0' and overview()['route']=='earth'
assert catalog()['survey_count']>=7 and catalog()['target_count']>=6
assert readiness()['ok'] is True
assert state('m31','dss-optical')['truth']['local_orientation_is_survey_imagery'] is False
assert state('crab','rosat-soft-xray')['truth']['live_telescope_feed_claimed'] is False
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text()
assert 'data-scsi-astronomical-contract="astronomical-observation-v4300"' in html
assert '/app/assets/astronomical-observation-v4300.js' in sw
print('PASS: v4.12.0 astronomical observation release contract validated.')
