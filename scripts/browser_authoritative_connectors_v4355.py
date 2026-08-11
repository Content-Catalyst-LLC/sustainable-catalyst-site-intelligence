#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
main=(ROOT/"backend/app/main.py").read_text()
promotion=(ROOT/"promote_site_intelligence_v4_35_5_to_github_and_render_macos.sh").read_text()
assert 'data-scsi-release="4.35.5"' in index
assert 'const APP_VERSION="4.35.5"' in app
assert '/public/deployment-verification' in main and '/public/source-health-policy' in main
assert '/public/deployment-verification' in promotion and '/public/source-health-policy' in promotion
assert 'Deep gate:' not in promotion
for endpoint in (
    '/public/authoritative-connectors/usfws-nwi/wetlands',
    '/public/wetlands-inland-water/live/usfws-nwi',
    '/public/authoritative-connectors/epa-echo/facilities',
    '/public/industrial-manufacturing/live/epa-echo',
    '/public/water-sanitation/live/epa-echo',
    '/public/authoritative-connectors/nasa-firms/area',
    '/public/terrestrial-ecosystems/live/nasa-firms',
    '/public/authoritative-connectors/usda-nass/quick-stats',
    '/public/agriculture-food-systems/live/usda-nass',
    '/public/authoritative-connectors/nasa-cmr/graphql/collections',
    '/public/science-discovery/nasa-cmr-graphql',
): assert endpoint in main, endpoint
assert 'authoritative_connectors_v4355' in main
assert 'authoritative_api_audit_v4355' in main
for forbidden in ('/public/climate/state','/public/biodiversity/state','/public/mining-critical-materials/state','/public/exoplanet-habitability/state'):
    assert forbidden not in promotion
print('PASS: v4.35.5 authoritative connector expansion III browser/static gate')
