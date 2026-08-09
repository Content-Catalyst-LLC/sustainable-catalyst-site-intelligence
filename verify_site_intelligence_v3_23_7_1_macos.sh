#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v32371-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"

printf '
==> Running mandatory v4.3.0 global country selector hydration gate
'
"$PYTHON" "$ROOT/scripts/run_browser_gate_v32371.py" browser_country_selector_hydration_v32371.py

printf '\n==> Running mandatory v4.3.0 global country truth browser gate\n'
"$PYTHON" "$ROOT/scripts/run_browser_gate_v32371.py" browser_global_country_data_truth_v32371.py

rm -rf "$BACKEND/backend"
printf '
==> Running complete inherited and v4.3.0 test suite with process-isolated teardown
'
PYTHONPATH="$BACKEND" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" "$ROOT/scripts/run_v32371_test_groups.py"
printf '
==> Verifying v4.3.0 global country data truth and coverage matrix
'
"$PYTHON" "$ROOT/scripts/validate_v32371_release.py"
grep -q 'APP_VERSION = "4.3.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.3.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.3.0"' "$BACKEND/public_app/service-worker.js"
grep -q '/public/data-truth/coverage-matrix' "$BACKEND/app/main.py"
grep -q 'data-truth-v32371.js?v=4.3.0' "$BACKEND/public_app/index.html"
grep -q 'data-truth-v32371.js' "$BACKEND/public_app/service-worker.js"
grep -q 'const countryCatalogTask=hydrateCountrySelector(initialCountry)' "$BACKEND/public_app/assets/app.js"
grep -q '/public/data-truth/countries' "$BACKEND/public_app/assets/app.js"
grep -q 'scsi:country-catalog-ready' "$BACKEND/public_app/assets/app.js"
grep -q 'scsi:country-catalog-ready' "$BACKEND/public_app/assets/data-truth-v32371.js"
grep -q '/public/mutation-observer-recovery' "$BACKEND/app/main.py"
grep -q 'summary.textContent!==nextText' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'requestAnimationFrame(flushMapSummaries)' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'state.observer?.disconnect()' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'MAX_SUMMARY_PASSES_PER_SECOND=8' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
grep -q 'SCSI_FIXED_WORDPRESS_EMBED' "$BACKEND/public_app/assets/embed-isolation-v32363.js"
grep -q 'data-scsi-fixed-app' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q 'parsed + 8' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js"
! grep -q 'new MutationObserver(()=>updateMapSummaries())' "$BACKEND/public_app/assets/browser-reliability-v3235.js"
cmp -s "$BACKEND/public_app/assets/browser-reliability-v3235.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js"
printf '
==> Verifying immutable repository manifest
'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.3.0';assert m['file_count']==len(m['files'])
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
==> Running mandatory complete-shell Chromium browser gate
'
"$PYTHON" "$ROOT/scripts/run_browser_gate_v32371.py" browser_complete_shell_gate_v32362.py
printf '\n==> Running mandatory v4.3.0 production-soak route and service-worker gate\n'
"$PYTHON" "$ROOT/scripts/run_browser_gate_v32371.py" browser_production_soak_gate_v32364.py
printf '\n==> Running mandatory long-page WordPress embed gate\n'
"$PYTHON" "$ROOT/scripts/run_browser_gate_v32371.py" browser_wordpress_embed_gate_v32363.py
rm -rf "$BACKEND/backend"
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: runtime state cleanup failed.' >&2; exit 1; }
printf '
SUCCESS: Site Intelligence v4.3.0 passed country selector hydration and global selection repair validation.
Repository: %s
' "$ROOT"
