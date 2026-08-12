#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.22"' in index
assert 'Production controls ready' in app
for endpoint in ('/public/atmosphere/live/airnow','/public/climate/discovery/era5','/public/atmosphere/discovery/cams','/public/authoritative-connectors/airnow/current','/public/authoritative-connectors/copernicus-era5/catalogue','/public/authoritative-connectors/cams/catalogue'):
 assert endpoint in main,endpoint
print('PASS: v4.35.22 Climate/Atmosphere workspace connector closure browser/static gate')
