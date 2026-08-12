#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.19"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/authoritative-connectors/osm-mining','/public/mining-critical-materials/live/osm-mining','/public/authoritative-connectors/usgs-usmin/discovery','/public/mining-critical-materials/discovery/usgs-usmin','/public/authoritative-connectors/usgs-mcs-2026/discovery','/public/mining-critical-materials/discovery/usgs-mcs-2026','/public/authoritative-connectors/osm-industrial','/public/industrial-manufacturing/live/osm-industrial','/public/authoritative-connectors/wits/trade-stats','/public/industrial-manufacturing/live/wits'):
    assert endpoint in main,endpoint
print('PASS: v4.35.19 Mining/Critical Materials/Industrial workspace connector closure browser/static gate')
