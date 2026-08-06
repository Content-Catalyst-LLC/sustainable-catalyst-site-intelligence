#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v32362-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
rm -rf "$BACKEND/backend"
printf '
==> Verifying v3.23.8 mutation observer recovery and complete-shell browser gate
'
"$PYTHON" "$ROOT/scripts/validate_v32362_release.py"
grep -q 'APP_VERSION = "3.23.8"' "$BACKEND/app/version.py"
grep -q 'Version: 3.23.8' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="3.23.8"' "$BACKEND/public_app/service-worker.js"
grep -q '/public/mutation-observer-recovery' "$BACKEND/app/main.py"
grep -q 'summary.textContent!==nextText' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'requestAnimationFrame(flushMapSummaries)' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'state.observer?.disconnect()' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'MAX_SUMMARY_PASSES_PER_SECOND=8' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
! grep -q 'new MutationObserver(()=>updateMapSummaries())' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
cmp -s "$BACKEND/public_app/assets/browser-reliability-v3235.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js"
printf '
==> Verifying immutable repository manifest
'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='3.23.8';assert m['file_count']==len(m['files'])
for e in m['files']:
 p=root/e['path'];d=p.read_bytes();assert len(d)==e['bytes'],e['path'];assert hashlib.sha256(d).hexdigest()==e['sha256'],e['path']
print(f"Verified {len(m['files'])} manifest entries.")
PYVERIFY
printf '
==> Compiling Python modules
'
"$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests" "$ROOT/scripts"
printf '
==> Parsing JSON and GeoJSON files
'
"$PYTHON" - "$ROOT" <<'PYJSON'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]);files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts]
for p in files:json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then
 printf '
==> Checking JavaScript syntax
';count=0
 while IFS= read -r -d '' f; do node --check "$f" >/dev/null;count=$((count+1));done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)
 printf 'Validated %s JavaScript files.
' "$count"
fi
if command -v php >/dev/null 2>&1; then printf '
==> Checking WordPress PHP syntax
';php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php";fi
printf '
==> Running complete inherited and v3.23.8 test suite with process-isolated teardown
'
PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/run_v32362_test_groups.py"
printf '
==> Running mandatory complete-shell Chromium browser gate
'
"$PYTHON" "$ROOT/scripts/browser_complete_shell_gate_v32362.py"
rm -rf "$BACKEND/backend"
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: runtime state cleanup failed.' >&2; exit 1; }
printf '
SUCCESS: Site Intelligence v3.23.8 passed mutation observer recovery and complete-shell browser validation.
Repository: %s
' "$ROOT"
