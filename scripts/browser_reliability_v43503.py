#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / "backend/public_app/index.html").read_text()
truth = (ROOT / "backend/public_app/assets/production-truth-v3231.js").read_text()
astro = (ROOT / "backend/public_app/assets/astronomical-observation-v4300.js").read_text()
app = (ROOT / "backend/public_app/assets/app.js").read_text()
main = (ROOT / "backend/app/main.py").read_text()
connectors = (ROOT / "backend/app/authoritative_connectors_v4353.py").read_text()
assert 'data-scsi-release="4.35.3"' in index
assert 'const VERSION="4.35.3"' in truth or "const VERSION='4.35.3'" in truth
assert "configurationRequired" in truth
assert "|unavailable|" not in truth
assert 'exoplanet-habitability-v43500.js?v=4.35.3' in astro
assert 'AUTHORITATIVE API COVERAGE' in index
assert 'authoritativeCompletedTargets' in index
assert '/public/authoritative-apis' in app
assert 'renderAuthoritativeApiAudit' in app
for route in (
    '/public/authoritative-connectors',
    '/public/hydrology/live/usgs-water',
    '/public/ocean-intelligence/erddap/search',
    '/public/ocean-intelligence/erddap/data',
    '/public/exoplanet-habitability/live',
    '/public/humanitarian-intelligence/displacement/live',
    '/public/science-discovery/nasa-cmr',
):
    assert route in main
for token in ('usgs-water-ogc-v0','noaa-coastwatch-erddap','nasa-exoplanet-tap','unhcr-refugee-statistics-v1','nasa-cmr-search'):
    assert token in connectors
print("PASS: v4.35.3 authoritative connector browser/static asset gate")
