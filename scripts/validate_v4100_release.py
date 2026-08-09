#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.orbital_earth_v4100 import overview,catalog,state,readiness
from app.unified_public_intelligence_v4000 import public_unified_navigation

o=overview(); c=catalog(); s=state('true-color','2026-08-01',0,20,1200); r=readiness(); nav=public_unified_navigation()
assert o['ok'] and o['version']=='4.3.0' and o['contract']=='orbital-earth-satellite-observation' and o['route']=='earth'
assert c['layer_count']>=8 and all(row['real_time_position_available'] is False for row in c['layers'])
assert 'gibs.earthdata.nasa.gov' in s['observation']['tile_url']
assert s['orbit_context']['real_time_spacecraft_position'] is None and s['orbit_context']['ground_track'] is None
assert s['footprints']['instantaneous_sensor_swath'] is None
assert r['ok'] and all(r['checks'].values())
assert nav['route_count']==35 and nav['primary_area_count']==6 and any(x['route_id']=='earth' for x in nav['routes'])
html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text(); js=(ROOT/'backend/public_app/assets/orbital-earth-v4100.js').read_text(); css=(ROOT/'backend/public_app/assets/orbital-earth-v4100.css').read_text()
assert 'data-scsi-release="4.3.0"' in html and 'data-scsi-orbital-contract="orbital-earth-v4100"' in html
assert 'orbital-earth-v4100.js?v=4.3.0' in html and 'orbital-earth-v4100.css?v=4.3.0' in html
assert 'orbital-earth-v4100.js' in sw and 'orbital-earth-v4100.css' in sw
assert 'SCSIOrbitalEarthV4100' in js and '.earth-globe-shell' in css
assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.js').read_text()
assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.css').read_text()
print(json.dumps({'version':'4.3.0','contract':o['contract'],'layers':c['layer_count'],'routes':nav['route_count'],'primary_areas':nav['primary_area_count'],'readiness':r['ok'],'state_sha256':s['state_sha256']},indent=2))
print('PASS: Site Intelligence v4.3.0 Orbital Earth & Satellite Observation contracts are complete.')
