#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.12"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/authoritative-connectors/faostat/data','/public/authoritative-connectors/ilostat/indicator','/public/authoritative-connectors/oecd/sdmx','/public/authoritative-connectors/epa-frs/facilities','/public/authoritative-connectors/usgs-volcano/notices'):
 assert endpoint in main,endpoint
print('PASS: v4.35.12 authoritative connector expansion IV browser/static gate')
