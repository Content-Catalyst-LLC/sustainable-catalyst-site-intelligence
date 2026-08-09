#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v4100-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"

printf '\n==> Validating v4.7.0 Orbital Earth contracts\n'
PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/validate_v4100_release.py"
grep -q 'APP_VERSION = "4.7.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.7.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.7.0"' "$BACKEND/public_app/service-worker.js"
grep -q 'data-scsi-orbital-contract="orbital-earth-v4100"' "$BACKEND/public_app/index.html"
for endpoint in '/public/orbital-earth' '/public/orbital-earth/catalog' '/public/orbital-earth/state' '/public/orbital-earth/export-manifest' '/public/orbital-earth/readiness' '/public/v4/readiness' '/public/data-truth/control-plane'; do grep -q "$endpoint" "$BACKEND/app/main.py"; done
cmp -s "$BACKEND/public_app/assets/orbital-earth-v4100.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.js"
cmp -s "$BACKEND/public_app/assets/orbital-earth-v4100.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.css"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.7.0';assert m['file_count']==len(m['files'])
for e in m['files']:
 p=root/e['path'];d=p.read_bytes();assert len(d)==e['bytes'],e['path'];assert hashlib.sha256(d).hexdigest()==e['sha256'],e['path']
print(f"Verified {len(m['files'])} manifest entries.")
PYVERIFY

printf '\n==> Compiling Python modules\n'
"$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests" "$ROOT/scripts"
printf '\n==> Parsing JSON and GeoJSON files\n'
"$PYTHON" - "$ROOT" <<'PYJSON'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts and p.name!='MANIFEST.json']
for p in files: json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then printf '\n==> Checking JavaScript syntax\n'; node "$ROOT/scripts/check_javascript_v4100.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then printf '\n==> Checking WordPress PHP syntax\n'; php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
printf '\n==> Running security static scan\n'
"$PYTHON" "$ROOT/scripts/security_static_scan_v4100.py"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then printf '\n==> Running complete inherited and v4.7.0 regression suite\n'; PYTHON="$PYTHON" PYTHONPATH="$BACKEND" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" "$ROOT/scripts/run_v4100_test_suite.py"; fi
if [[ "${SC_SI_RUN_BROWSER_GATE:-0}" == "1" && "${SC_SI_SKIP_BROWSER:-0}" != "1" ]]; then printf '\n==> Running v4.7.0 orbital browser interaction gate\n'; PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/browser_orbital_earth_v4100.py"; else echo '==> Orbital browser gate is a build-time package gate and is not repeated by default inside the installer verifier.'; fi
rm -rf "$BACKEND/backend"
printf '\nSUCCESS: Site Intelligence v4.7.0 passed Orbital Earth & Satellite Observation validation.\nRepository: %s\n' "$ROOT"
