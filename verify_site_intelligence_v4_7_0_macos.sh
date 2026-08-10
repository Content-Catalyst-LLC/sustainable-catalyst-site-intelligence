#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-python3}"
grep -q 'APP_VERSION = "4.17.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.17.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
for endpoint in /public/orbital-earth /public/planetary-intelligence /public/astronomical-observation /public/solar-system-navigation /public/ocean-intelligence /public/water-column /public/seafloor-intelligence /public/seafloor-intelligence/catalog /public/seafloor-intelligence/state /public/seafloor-intelligence/sample/normalize /public/seafloor-intelligence/footprint/normalize /public/seafloor-intelligence/export-manifest /public/seafloor-intelligence/readiness /public/v4/readiness; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
for asset in ocean-surface-v4500 water-column-v4600 seafloor-bathymetry-v4700; do
  cmp -s "$BACKEND/public_app/assets/${asset}.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.js"
  cmp -s "$BACKEND/public_app/assets/${asset}.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.css"
done
"$PYTHON" "$ROOT/scripts/validate_v4700_release.py"
echo '==> Verifying immutable repository manifest'
"$PYTHON" - "$ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
assert m.get('release')=='4.17.0'
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
if command -v node >/dev/null 2>&1; then node "$ROOT/scripts/check_javascript_v4700.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
"$PYTHON" "$ROOT/scripts/security_static_scan_v4700.py" "$ROOT"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q); fi
if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/browser_seafloor_bathymetry_v4700.py"; fi
echo 'SUCCESS: Site Intelligence v4.17.0 passed Seafloor & Bathymetric Intelligence validation.'
