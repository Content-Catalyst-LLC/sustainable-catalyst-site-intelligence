#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/"backend/public_app/index.html").read_text()
app=(ROOT/"backend/public_app/assets/app.js").read_text()
main=(ROOT/"backend/app/main.py").read_text()
promotion=(ROOT/"promote_site_intelligence_v4_35_6_to_github_and_render_macos.sh").read_text()
assert 'data-scsi-release="4.35.14"' in index
assert 'const APP_VERSION="4.35.14"' in app
assert '/public/deployment-verification' in main and '/public/source-health-policy' in main
assert '/public/deployment-verification' in promotion and '/public/source-health-policy' in promotion
assert 'Deep gate:' not in promotion
for endpoint in (
    '/public/authoritative-connectors/pcbs/pxweb/metadata',
    '/public/authoritative-connectors/pcbs/pxweb/data',
    '/public/country-statistics/palestine/pcbs/data',
    '/public/authoritative-connectors/statcan/vectors',
    '/public/country-statistics/canada/statcan',
    '/public/authoritative-connectors/ons/observations',
    '/public/country-statistics/united-kingdom/ons',
    '/public/authoritative-connectors/abs/sdmx',
    '/public/country-statistics/australia/abs',
    '/public/authoritative-connectors/bls/timeseries',
    '/public/economics-labor/live/bls',
): assert endpoint in main, endpoint
assert 'authoritative_connectors_v4356' in main
assert 'authoritative_api_audit_v4356' in main
for forbidden in ('/public/climate/state','/public/biodiversity/state','/public/mining-critical-materials/state','/public/exoplanet-habitability/state'):
    assert forbidden not in promotion
print('PASS: v4.35.14 national statistical/domain-authority connector browser/static gate')
