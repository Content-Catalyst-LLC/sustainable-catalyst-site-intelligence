#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.22"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/authoritative-connectors/osm-water','/public/water-sanitation/live/osm-water','/public/authoritative-connectors/epa-sdwis','/public/water-sanitation/live/epa-sdwis','/public/authoritative-connectors/nidis-drought/file','/public/hydrology/live/drought-gov','/public/authoritative-connectors/nasa-gpm/discovery','/public/hydrology/discovery/nasa-gpm','/public/authoritative-connectors/glofas/layers','/public/hydrology/discovery/glofas'):
 assert endpoint in main,endpoint
print('PASS: v4.35.22 Water/Hydrology/Sanitation workspace connector closure browser/static gate')
