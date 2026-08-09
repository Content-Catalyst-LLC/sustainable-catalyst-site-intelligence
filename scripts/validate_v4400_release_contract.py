from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.solar_system_navigation_v4400 import overview,catalog,readiness,state
assert overview()['version']=='4.8.0' and overview()['route']=='earth'
assert catalog()['body_count']>=10 and catalog()['mission_context_count']>=6
assert readiness()['ok'] is True
s=state('jupiter','juno')
assert s['ephemeris']['authoritative_solution_loaded'] is False
assert s['truth']['spacecraft_position_fabricated'] is False and s['truth']['trajectory_fabricated'] is False
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text()
assert 'data-scsi-solar-system-contract="solar-system-navigation-v4400"' in html
assert '/app/assets/solar-system-navigation-v4400.js' in sw
print('PASS: v4.8.0 solar-system navigation release contract validated.')
