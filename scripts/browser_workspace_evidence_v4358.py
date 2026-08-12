#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text()
app=(ROOT/'backend/public_app/assets/app.js').read_text()
main=(ROOT/'backend/app/main.py').read_text()
truth=(ROOT/'backend/public_app/assets/record-provenance-v3238.js').read_text()
promotion=(ROOT/'promote_site_intelligence_v4_35_8_to_github_and_render_macos.sh').read_text()
assert 'data-scsi-release="4.35.13"' in index
assert 'data-canonical-observation' in app
assert 'data-record-truth-indicator' in app
assert 'Canonical observation' in truth and 'Canonical SHA-256' in truth
for endpoint in ('/public/workspace-evidence','/public/workspace-evidence/readiness','/public/workspace-evidence/country/{country_code}','/public/workspace-evidence/country/{country_code}/indicator/{indicator_id}'):
    assert endpoint in main,endpoint
assert 'record_provenance_v4358' in main
assert 'Deep gate:' not in promotion
for forbidden in ('/public/climate/state','/public/biodiversity/state','/public/mining-critical-materials/state','/public/exoplanet-habitability/state'):
    assert forbidden not in promotion
print('PASS: v4.35.13 workspace-evidence browser/static gate')
