#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-python3}"
grep -q 'APP_VERSION = "4.23.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.23.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
for endpoint in /public/orbital-earth /public/planetary-intelligence /public/astronomical-observation /public/solar-system-navigation /public/ocean-intelligence /public/water-column /public/seafloor-intelligence /public/underwater-observation /public/marine-biodiversity /public/ocean-missions /public/ocean-events /public/marine-human-activity /public/marine-pollution /public/coastal-change /public/ocean-governance /public/cryosphere /public/atmosphere /public/hydrology /public/hydrology/catalog /public/hydrology/state /public/hydrology/measurement/normalize /public/hydrology/forecast/normalize /public/hydrology/threshold/preview /public/hydrology/export-manifest /public/hydrology/readiness /public/terrestrial-ecosystems /public/terrestrial-ecosystems/catalog /public/terrestrial-ecosystems/state /public/terrestrial-ecosystems/measurement/normalize /public/terrestrial-ecosystems/feature/normalize /public/terrestrial-ecosystems/threshold/preview /public/terrestrial-ecosystems/export-manifest /public/terrestrial-ecosystems/readiness /public/geosphere /public/geosphere/catalog /public/geosphere/state /public/geosphere/measurement/normalize /public/geosphere/notice/normalize /public/geosphere/threshold/preview /public/geosphere/export-manifest /public/geosphere/readiness /public/soils-land /public/soils-land/catalog /public/soils-land/state /public/soils-land/measurement/normalize /public/soils-land/assessment/normalize /public/soils-land/threshold/preview /public/soils-land/export-manifest /public/soils-land/readiness /public/climate /public/climate/catalog /public/climate/state /public/climate/measurement/normalize /public/climate/extreme/normalize /public/climate/threshold/preview /public/climate/export-manifest /public/climate/readiness /public/biodiversity /public/biodiversity/catalog /public/biodiversity/state /public/biodiversity/occurrence/normalize /public/biodiversity/conservation/normalize /public/biodiversity/overlap/preview /public/biodiversity/export-manifest /public/biodiversity/readiness /public/v4/readiness; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
for asset in ocean-surface-v4500 water-column-v4600 seafloor-bathymetry-v4700 underwater-observation-v4800 marine-biodiversity-v4900 ocean-missions-v41000 ocean-events-v41100 marine-human-activity-v41200 marine-pollution-v41300 coastal-change-v41400 ocean-governance-v41500 cryosphere-v41600 atmosphere-v41700 hydrology-v41800 terrestrial-ecosystems-v41900 geosphere-v42000 soils-land-v42100 climate-v42200 biodiversity-v42300; do
  cmp -s "$BACKEND/public_app/assets/${asset}.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.js"
  cmp -s "$BACKEND/public_app/assets/${asset}.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.css"
done
"$PYTHON" "$ROOT/scripts/validate_v42300_release.py"
echo '==> Verifying immutable repository manifest'
"$PYTHON" - "$ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
assert m.get('release')=='4.23.0'
assert not any(row['path'].startswith('backend/backend/') for row in m['files'])
for row in m['files']:
 p=root/row['path']; assert p.is_file(),row['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print(f"Verified {len(m['files'])} manifest entries.")
PY
echo '==> Parsing JSON/GeoJSON'
"$PYTHON" - "$ROOT" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for p in root.rglob('*'):
 if p.is_file() and p.suffix.lower() in {'.json','.geojson'} and p.name!='MANIFEST.json': json.loads(p.read_text()); rows.append(p)
print(f"Parsed {len(rows)} JSON/GeoJSON files.")
PY
if command -v node >/dev/null 2>&1; then node "$ROOT/scripts/check_javascript_v42300.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
"$PYTHON" "$ROOT/scripts/security_static_scan_v41100.py" "$ROOT"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q); fi
if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/browser_biodiversity_v42300.py"; fi
echo 'SUCCESS: Site Intelligence v4.23.0 passed Global Biodiversity, Species Distribution & Conservation Intelligence validation.'
