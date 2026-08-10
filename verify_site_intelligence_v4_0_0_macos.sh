#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v4000-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
reset_runtime(){ rm -rf "$RUNTIME_SANDBOX"; mkdir -p "$RUNTIME_SANDBOX"; }

printf '
==> Validating v4.16.0 Unified Public Intelligence Platform contracts
'
PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/validate_v4000_release.py"
grep -q 'APP_VERSION = "4.16.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.16.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.16.0"' "$BACKEND/public_app/service-worker.js"
grep -q 'data-scsi-platform-contract="unified-v4"' "$BACKEND/public_app/index.html"
for endpoint in \
  '/public/v4' \
  '/public/v4/navigation' \
  '/public/v4/contracts' \
  '/public/v4/readiness' \
  '/public/data-truth/control-plane' \
  '/public/workspaces/unified-state' \
  '/public/record-truth/manifest' \
  '/public/publication-studio' \
  '/public/institutional-governance' \
  '/public/production-assurance'; do
  grep -q "$endpoint" "$BACKEND/app/main.py"
done
grep -q 'unified-platform-v4000.js?v=4.16.0' "$BACKEND/public_app/index.html"
grep -q 'unified-platform-v4000.css?v=4.16.0' "$BACKEND/public_app/index.html"
grep -q 'unified-platform-v4000.js' "$BACKEND/public_app/service-worker.js"
grep -q 'SCSIUnifiedPlatformV4000' "$BACKEND/public_app/assets/unified-platform-v4000.js"
cmp -s "$BACKEND/public_app/assets/unified-platform-v4000.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.js"
cmp -s "$BACKEND/public_app/assets/unified-platform-v4000.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/unified-platform-v4000.css"

printf '
==> Verifying immutable repository manifest
'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.16.0';assert m['file_count']==len(m['files'])
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
root=Path(sys.argv[1]);files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts and p.name!='MANIFEST.json']
for p in files: json.loads(p.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then
  printf '
==> Checking JavaScript syntax
'
  node "$ROOT/scripts/check_javascript_v4000.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"
fi
if command -v php >/dev/null 2>&1; then printf '
==> Checking WordPress PHP syntax
'; php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi

printf '
==> Running security and supply-chain static scan
'
"$PYTHON" "$ROOT/scripts/security_static_scan_v4000.py"
if ! "$PYTHON" -m pip check >/dev/null 2>&1; then
  if [[ "${SC_SI_STRICT_DEPENDENCIES:-0}" == "1" ]]; then echo 'ERROR: pip dependency check failed.' >&2; exit 1; fi
  echo 'WARN: pip check reported unrelated environment conflicts; installer validation uses a clean isolated virtual environment.' >&2
fi
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then
  printf '
==> Running complete inherited and v4.16.0 regression suite
'
  reset_runtime
  PYTHON="$PYTHON" PYTHONPATH="$BACKEND" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" "$ROOT/scripts/run_v4000_test_suite.py"
else
  printf '
==> Skipping repeated Python regression suite by explicit verifier policy
'
fi
if [[ "${SC_SI_RUN_BROWSER_GATE:-0}" == "1" && "${SC_SI_SKIP_BROWSER:-0}" != "1" ]]; then
  printf '
==> Running v4.16.0 browser consolidation gate
'
  reset_runtime
  PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/browser_unified_platform_v4000.py"
else
  printf '
==> Browser consolidation gate not repeated inside installer verifier; immutable-package browser validation is a build-time gate
'
fi
rm -rf "$BACKEND/backend"
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: runtime state cleanup failed.' >&2; exit 1; }
printf '
SUCCESS: Site Intelligence v4.16.0 passed Unified Public Intelligence Platform validation.
Repository: %s
' "$ROOT"
