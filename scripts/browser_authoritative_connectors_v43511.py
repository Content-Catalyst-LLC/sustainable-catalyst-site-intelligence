#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.16"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/energy-systems/live/osm-power','/public/energy-systems/live/eia','/public/energy-systems/live/ember','/public/energy-systems/live/entsoe','/public/digital-connectivity/live/osm-telecom','/public/digital-connectivity/discovery/mlab','/public/digital-connectivity/discovery/fcc-bdc'):
 assert endpoint in main,endpoint
print('PASS: v4.35.16 Energy/Digital workspace connector closure browser/static gate')
