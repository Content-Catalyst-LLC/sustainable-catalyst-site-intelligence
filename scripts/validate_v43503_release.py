#!/usr/bin/env python3
from pathlib import Path
import json, os, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "MANIFEST.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    assert not any(row["path"].startswith("backend/backend/") for row in manifest.get("files", []))
assert not (ROOT / "backend/backend").exists()
assert 'APP_VERSION = "4.35.3"' in (ROOT / "backend/app/version.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
for endpoint in (
    '/public/authoritative-apis','/public/authoritative-apis/catalog','/public/authoritative-apis/workspaces','/public/authoritative-apis/readiness',
    '/public/authoritative-connectors','/public/authoritative-connectors/readiness',
    '/public/authoritative-connectors/usgs-water/latest','/public/authoritative-connectors/noaa-erddap/search','/public/authoritative-connectors/noaa-erddap/data',
    '/public/authoritative-connectors/nasa-exoplanets','/public/authoritative-connectors/unhcr-population','/public/authoritative-connectors/nasa-cmr/collections',
    '/public/hydrology/live/usgs-water','/public/ocean-intelligence/erddap/search','/public/ocean-intelligence/erddap/data','/public/exoplanet-habitability/live',
    '/public/humanitarian-intelligence/displacement/live','/public/science-discovery/nasa-cmr','/public/v4/configuration-readiness',
):
    assert f'@app.get("{endpoint}")' in main
connectors=(ROOT/'backend/app/authoritative_connectors_v4353.py').read_text()
for interface in ('usgs-water-ogc-v0','noaa-coastwatch-erddap','nasa-exoplanet-tap','unhcr-refugee-statistics-v1','nasa-cmr-search'):
    assert interface in connectors
for integrity in ('Missing source values remain missing','Nulls remain null','not a measured surface temperature','official periodic aggregate statistics','not observation values'):
    assert integrity.lower() in connectors.lower()
audit=(ROOT/'backend/app/authoritative_api_audit_v4353.py').read_text()
assert 'COMPLETED_CONNECTOR_TARGETS' in audit
assert '"api.waterdata.usgs.gov": ("LIVE"' in audit
assert '"cmr.earthdata.nasa.gov": ("DISCOVERY"' in audit
humanitarian=(ROOT/'backend/app/humanitarian_intelligence.py').read_text()
assert 'https://api.reliefweb.int/v2' in humanitarian and 'https://api.reliefweb.int/v1' not in humanitarian
render=(ROOT/'render.yaml').read_text()
assert 'site-intelligence-v4.35.3' in render and 'SC_SI_USGS_WATER_API_KEY' in render
index=(ROOT/'backend/public_app/index.html').read_text(); app_js=(ROOT/'backend/public_app/assets/app.js').read_text()
assert 'AUTHORITATIVE API COVERAGE' in index and 'authoritativeCompletedTargets' in index
assert 'completed_connector_targets' in app_js
plugin=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.35.3' in plugin and 'site-intelligence-v4.35.3' in plugin
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43503_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.35.3 static release validation')
