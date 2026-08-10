#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3250-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
reset_runtime(){ rm -rf "$RUNTIME_SANDBOX"; mkdir -p "$RUNTIME_SANDBOX"; }

printf '\n==> Running complete inherited and v4.17.0 test suite\n'
PYTHON="$PYTHON" PYTHONPATH="$BACKEND" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" "$ROOT/scripts/run_v3250_test_suite.py"
rm -rf "$BACKEND/backend"

printf '\n==> Validating unified analytical state contracts\n'
PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/validate_v3250_release.py"
grep -q 'APP_VERSION = "4.17.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.17.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.17.0"' "$BACKEND/public_app/service-worker.js"
grep -q '/public/workspaces/unified-state' "$BACKEND/app/main.py"
grep -q '/public/workspaces/unified-state/normalize' "$BACKEND/app/main.py"
grep -q '/public/workspaces/unified-state/deep-link' "$BACKEND/app/main.py"
grep -q '/public/workspaces/unified-state/handoff/{target}' "$BACKEND/app/main.py"
grep -q 'cross-view-state-v3250.js?v=4.17.0' "$BACKEND/public_app/index.html"
grep -q 'cross-view-state-v3250.js' "$BACKEND/public_app/service-worker.js"
grep -q 'SiteIntelligenceCrossViewState' "$BACKEND/public_app/assets/cross-view-state-v3250.js"
cmp -s "$BACKEND/public_app/assets/cross-view-state-v3250.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/cross-view-state-v3250.js"
cmp -s "$BACKEND/public_app/assets/cross-view-state-v3250.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/cross-view-state-v3250.css"

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
for p in files: json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then
  printf '\n==> Checking JavaScript syntax\n'
  node "$ROOT/scripts/check_javascript_v3250.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"
fi
if command -v php >/dev/null 2>&1; then printf '\n==> Checking WordPress PHP syntax\n'; php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi

for gate in \
  browser_cross_view_state_v3250.py \
  browser_country_selector_interaction_v3238.py \
  browser_country_selector_hydration_v3238.py \
  browser_global_country_data_truth_v3238.py \
  browser_record_provenance_v3238.py \
  browser_data_truth_control_plane_v3240.py \
  browser_complete_shell_gate_v32362.py \
  browser_production_soak_gate_v32364.py \
  browser_wordpress_embed_gate_v32363.py; do
  printf '\n==> Running browser gate: %s\n' "$gate"
  reset_runtime
  "$PYTHON" "$ROOT/scripts/run_browser_gate_v3250.py" "$gate"
done

rm -rf "$BACKEND/backend"
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: runtime state cleanup failed.' >&2; exit 1; }
printf '\nSUCCESS: Site Intelligence v4.17.0 passed unified analytical workspace and cross-view state validation.\nRepository: %s\n' "$ROOT"
