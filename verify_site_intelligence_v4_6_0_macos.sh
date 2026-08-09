#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-python3}"
grep -q 'APP_VERSION = "4.11.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.11.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
for endpoint in /public/orbital-earth /public/planetary-intelligence /public/astronomical-observation /public/solar-system-navigation /public/ocean-intelligence /public/ocean-intelligence/catalog /public/ocean-intelligence/state /public/ocean-intelligence/observation/normalize /public/ocean-intelligence/export-manifest /public/ocean-intelligence/readiness /public/water-column /public/water-column/catalog /public/water-column/state /public/water-column/profile/normalize /public/water-column/depth/resolve /public/water-column/export-manifest /public/water-column/readiness /public/v4/readiness; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
cmp -s "$BACKEND/public_app/assets/ocean-surface-v4500.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/ocean-surface-v4500.js"
cmp -s "$BACKEND/public_app/assets/ocean-surface-v4500.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/ocean-surface-v4500.css"
cmp -s "$BACKEND/public_app/assets/water-column-v4600.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.js"
cmp -s "$BACKEND/public_app/assets/water-column-v4600.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.css"
"$PYTHON" "$ROOT/scripts/validate_v4600_release.py"
echo '==> Verifying immutable repository manifest'
"$PYTHON" - "$ROOT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
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
if command -v node >/dev/null 2>&1; then node "$ROOT/scripts/check_javascript_v4600.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
"$PYTHON" "$ROOT/scripts/security_static_scan_v4600.py" "$ROOT"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q); fi
if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/browser_water_column_v4600.py"; fi
echo 'SUCCESS: Site Intelligence v4.11.0 passed Water Column & Depth Explorer validation.'
