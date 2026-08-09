#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; BACKEND="$ROOT/backend"; PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3234-runtime.XXXXXX")"; trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"; rm -rf "$BACKEND/backend"
printf '
==> Verifying v4.2.0 analytical workspace contracts
'
grep -q 'APP_VERSION = "4.2.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.2.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.2.0"' "$BACKEND/public_app/service-worker.js"
grep -q 'analytical-workspaces-v3234.js' "$BACKEND/public_app/index.html"
grep -q '/public/workflows/analytical' "$BACKEND/app/main.py"
grep -q 'SCSIAnalyticalWorkspacesV3234' "$BACKEND/public_app/assets/analytical-workspaces-v3234.js"
grep -q 'analyticalWorkspacesJsUrl' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q "wp_enqueue_script('scsi-analytical-workspaces'" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
printf '
==> Verifying immutable repository manifest
'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.2.0';assert m['file_count']==len(m['files'])
for e in m['files']:
 p=root/e['path'];d=p.read_bytes();assert len(d)==e['bytes'],e['path'];assert hashlib.sha256(d).hexdigest()==e['sha256'],e['path']
print(f"Verified {len(m['files'])} manifest entries.")
PYVERIFY
printf '
==> Compiling Python modules
'; "$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests" "$ROOT/scripts"
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
if command -v node >/dev/null 2>&1; then printf '
==> Checking JavaScript syntax
';count=0;while IFS= read -r -d '' f;do node --check "$f" >/dev/null;count=$((count+1));done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0);printf 'Validated %s JavaScript files.
' "$count";fi
if command -v php >/dev/null 2>&1;then printf '
==> Checking WordPress PHP syntax
';php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php";fi
printf '
==> Running all tests with adaptive process isolation
';PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/run_v3234_test_groups.py"
if [[ "${SC_SI_SKIP_BROWSER_SMOKE:-0}" != "1" ]];then printf '
==> Running Chromium smoke tests when available
';for n in 3230 3231 3232 3233 3234;do "$PYTHON" "$ROOT/scripts/browser_smoke_v${n}.py";done;fi
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: tests wrote runtime state into immutable checkout.' >&2;exit 1; }
printf '
SUCCESS: Site Intelligence v4.2.0 passed deterministic validation.
Repository: %s
' "$ROOT"
