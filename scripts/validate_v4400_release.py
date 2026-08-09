#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.solar_system_navigation_v4400 import overview,catalog,state,readiness
from app.unified_public_intelligence_v4000 import public_unified_navigation
o=overview();c=catalog();s=state('jupiter','juno','2026-08-09T06:32:00Z','ECLIPJ2000','earth-center');r=readiness();nav=public_unified_navigation()
assert o['ok'] and o['version']=='4.5.0' and o['route']=='earth'
assert c['body_count']>=10 and c['mission_context_count']>=6 and c['service_count']>=3
assert s['ephemeris']['authoritative_solution_loaded'] is False
assert s['truth']['local_orbit_layout_is_ephemeris'] is False and s['truth']['trajectory_fabricated'] is False
assert r['ok'] and all(r['checks'].values())
assert nav['route_count']==35 and nav['primary_area_count']==6
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text(); js=(ROOT/'backend/public_app/assets/solar-system-navigation-v4400.js').read_text(); css=(ROOT/'backend/public_app/assets/solar-system-navigation-v4400.css').read_text()
assert 'data-scsi-release="4.5.0"' in html and 'data-scsi-solar-system-contract="solar-system-navigation-v4400"' in html
assert 'solar-system-navigation-v4400.js?v=4.5.0' in html and 'solar-system-navigation-v4400.css?v=4.5.0' in html
assert 'solar-system-navigation-v4400.js' in sw and 'solar-system-navigation-v4400.css' in sw
assert 'SCSISolarSystemV4400' in js and '.solar4400-stage' in css
assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/solar-system-navigation-v4400.js').read_text()
assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/solar-system-navigation-v4400.css').read_text()
print(json.dumps({'version':'4.5.0','contract':o['contract'],'bodies':c['body_count'],'missions':c['mission_context_count'],'routes':nav['route_count'],'primary_areas':nav['primary_area_count'],'readiness':r['ok'],'state_sha256':s['state_sha256']},indent=2))
print('PASS: Site Intelligence v4.5.0 Solar System Navigation & Mission Ephemeris contracts are complete.')
