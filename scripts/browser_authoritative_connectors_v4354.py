#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
main=(ROOT/"backend/app/main.py").read_text()
promotion=(ROOT/"promote_site_intelligence_v4_35_4_to_github_and_render_macos.sh").read_text()
assert 'data-scsi-release="4.35.4"' in index
assert 'const APP_VERSION="4.35.4"' in app
assert '/public/deployment-verification' in main
assert '/public/source-health-policy' in main
assert '/public/deployment-verification' in promotion
assert '/public/source-health-policy' in promotion
assert 'Deep gate:' not in promotion

for endpoint in (
    '/public/authoritative-connectors/noaa-coops/data',
    '/public/authoritative-connectors/noaa-ncei/data',
    '/public/authoritative-connectors/obis/occurrences',
    '/public/authoritative-connectors/eurostat/statistics',
    '/public/authoritative-connectors/usda-soils/mapunits',
    '/public/coastal-change/live/noaa-coops',
    '/public/climate/live/noaa-ncei',
    '/public/biodiversity/live/obis',
    '/public/solid-waste-circular-materials/live/eurostat',
    '/public/soils-land/live/usda-nrcs',
):
    assert endpoint in main, endpoint
assert 'authoritative_connectors_v4354' in main
for forbidden in ('/public/climate/state','/public/biodiversity/state','/public/mining-critical-materials/state','/public/exoplanet-habitability/state'):
    assert forbidden not in promotion
print("PASS: v4.35.4 authoritative connector expansion II browser/static gate")
