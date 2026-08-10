#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3235-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
rm -rf "$BACKEND/backend"

printf '\n==> Verifying v4.17.0 browser reliability contracts\n'
"$PYTHON" "$ROOT/scripts/validate_v3235_release.py"

grep -q 'APP_VERSION = "4.17.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.17.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.17.0"' "$BACKEND/public_app/service-worker.js"
grep -q 'browser-reliability-v3235.js' "$BACKEND/public_app/index.html"
grep -q '/public/browser-reliability' "$BACKEND/app/main.py"
grep -q 'browserReliabilityJsUrl' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q "wp_enqueue_script('scsi-browser-reliability'" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.17.0';assert m['file_count']==len(m['files'])
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
root=Path(sys.argv[1]);files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts]
for p in files:json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON

if command -v node >/dev/null 2>&1; then
  printf '\n==> Checking JavaScript syntax\n'
  count=0
  while IFS= read -r -d '' f; do node --check "$f" >/dev/null; count=$((count+1)); done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)
  printf 'Validated %s JavaScript files.\n' "$count"
fi
if command -v php >/dev/null 2>&1; then
  printf '\n==> Checking WordPress PHP syntax\n'
  php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
fi

printf '\n==> Running complete inherited test suite\n'
(
  cd "$BACKEND"
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q tests
)

if [[ "${SC_SI_SKIP_BROWSER_SMOKE:-0}" != "1" ]]; then
  printf '\n==> Running v4.17.0 Chromium reliability presentation check when available\n'
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3235.py"
fi
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: tests wrote runtime state into immutable checkout.' >&2; exit 1; }
printf '\nSUCCESS: Site Intelligence v4.17.0 passed deterministic validation.\nRepository: %s\n' "$ROOT"
