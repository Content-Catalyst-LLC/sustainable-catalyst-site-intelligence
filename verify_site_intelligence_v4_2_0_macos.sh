#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-$(command -v python3)}"
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v4200-runtime.XXXXXX")"; trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT; export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
printf '\n==> Validating v4.3.0 Lunar & Planetary Intelligence contracts\n'
PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/validate_v4200_release_contract.py"
grep -q 'APP_VERSION = "4.3.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.3.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.3.0"' "$BACKEND/public_app/service-worker.js"
for endpoint in '/public/orbital-earth' '/public/planetary-intelligence' '/public/planetary-intelligence/catalog' '/public/planetary-intelligence/state' '/public/planetary-intelligence/export-manifest' '/public/planetary-intelligence/readiness' '/public/v4/readiness'; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
cmp -s "$BACKEND/public_app/assets/planetary-intelligence-v4200.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/planetary-intelligence-v4200.js"
cmp -s "$BACKEND/public_app/assets/planetary-intelligence-v4200.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/planetary-intelligence-v4200.css"
printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.3.0';assert m['file_count']==len(m['files'])
for e in m['files']:
 p=root/e['path'];d=p.read_bytes();assert len(d)==e['bytes'],e['path'];assert hashlib.sha256(d).hexdigest()==e['sha256'],e['path']
print(f"Verified {len(m['files'])} manifest entries.")
PY
printf '\n==> Compiling Python modules\n'; "$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests" "$ROOT/scripts"
printf '\n==> Parsing JSON and GeoJSON files\n'; "$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts and p.name!='MANIFEST.json']
for p in files: json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PY
if command -v node >/dev/null 2>&1; then printf '\n==> Checking JavaScript syntax\n'; node "$ROOT/scripts/check_javascript_v4200.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then printf '\n==> Checking WordPress PHP syntax\n'; php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
printf '\n==> Running security static scan\n'; "$PYTHON" "$ROOT/scripts/security_static_scan_v4200.py"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then printf '\n==> Running complete regression suite\n'; (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q); fi
if [[ "${SC_SI_RUN_BROWSER_GATE:-0}" == "1" && "${SC_SI_SKIP_BROWSER:-0}" != "1" ]]; then printf '\n==> Running planetary browser interaction gate\n'; "$PYTHON" "$ROOT/scripts/browser_planetary_intelligence_v4200.py"; else echo '==> Planetary browser gate is a build-time package gate and is not repeated by default inside the installer verifier.'; fi
printf '\nSUCCESS: Site Intelligence v4.3.0 passed Lunar & Planetary Intelligence validation.\n'
