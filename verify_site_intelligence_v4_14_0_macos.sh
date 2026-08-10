#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-python3}"
grep -q 'APP_VERSION = "4.16.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.16.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
for endpoint in /public/orbital-earth /public/planetary-intelligence /public/astronomical-observation /public/solar-system-navigation /public/ocean-intelligence /public/water-column /public/seafloor-intelligence /public/underwater-observation /public/marine-biodiversity /public/ocean-missions /public/ocean-events /public/marine-human-activity /public/marine-pollution /public/marine-pollution/readiness /public/coastal-change /public/coastal-change/catalog /public/coastal-change/state /public/coastal-change/water-level/normalize /public/coastal-change/shoreline/normalize /public/coastal-change/habitat/normalize /public/coastal-change/scenario/preview /public/coastal-change/export-manifest /public/coastal-change/readiness /public/v4/readiness; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
for asset in ocean-surface-v4500 water-column-v4600 seafloor-bathymetry-v4700 underwater-observation-v4800 marine-biodiversity-v4900 ocean-missions-v41000 ocean-events-v41100 marine-human-activity-v41200 marine-pollution-v41300 coastal-change-v41400; do
  cmp -s "$BACKEND/public_app/assets/${asset}.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.js"
  cmp -s "$BACKEND/public_app/assets/${asset}.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.css"
done
"$PYTHON" "$ROOT/scripts/validate_v41400_release.py"
echo '==> Verifying immutable repository manifest'
"$PYTHON" - "$ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
assert m.get('release')=='4.16.0'
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
if command -v node >/dev/null 2>&1; then node "$ROOT/scripts/check_javascript_v41400.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
"$PYTHON" "$ROOT/scripts/security_static_scan_v41100.py" "$ROOT"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q); fi
if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/browser_coastal_change_v41400.py"; fi
echo 'SUCCESS: Site Intelligence v4.16.0 passed Coastal Change, Sea Level & Blue-Carbon Intelligence validation.'
