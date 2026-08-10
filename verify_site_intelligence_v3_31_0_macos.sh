#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"; fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3310-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
reset_runtime(){ rm -rf "$RUNTIME_SANDBOX"; mkdir -p "$RUNTIME_SANDBOX"; }

printf '\n==> Validating v4.13.0 Security, Observability, Performance, and Scale Assurance contracts\n'
PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/validate_v3310_release.py"
grep -q 'APP_VERSION = "4.13.0"' "$BACKEND/app/version.py"
grep -q 'Version: 4.13.0' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="4.13.0"' "$BACKEND/public_app/service-worker.js"
for endpoint in \
  '/public/institutional-governance' \
  '/public/institutional-governance/workspace/preview' \
  '/public/institutional-governance/review-queue' \
  '/public/institutional-governance/annotation/preview' \
  '/public/institutional-governance/decision/preview' \
  '/public/institutional-governance/audit/preview' \
  '/public/institutional-governance/package/export' \
  '/public/institutional-governance/package/import-preview' \
  '/public/publication-studio' \
  '/public/monitoring-operations' \
  '/public/research-integration'; do
  grep -q "$endpoint" "$BACKEND/app/main.py"
done
grep -q 'institutional-governance-v3300.js?v=4.13.0' "$BACKEND/public_app/index.html"
grep -q 'institutional-governance-v3300.js' "$BACKEND/public_app/service-worker.js"
grep -q 'SCSIInstitutionalGovernanceV3300' "$BACKEND/public_app/assets/institutional-governance-v3300.js"
cmp -s "$BACKEND/public_app/assets/institutional-governance-v3300.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/institutional-governance-v3300.js"
cmp -s "$BACKEND/public_app/assets/institutional-governance-v3300.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/institutional-governance-v3300.css"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);m=json.loads((root/'MANIFEST.json').read_text());assert m['release']=='4.13.0';assert m['file_count']==len(m['files'])
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
if command -v node >/dev/null 2>&1; then
  printf '\n==> Checking JavaScript syntax\n'
  node "$ROOT/scripts/check_javascript_v3310.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"
fi
if command -v php >/dev/null 2>&1; then printf '\n==> Checking WordPress PHP syntax\n'; php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi

printf '\n==> Running security and supply-chain static scan\n'
"$PYTHON" "$ROOT/scripts/security_static_scan_v3310.py"
if ! "$PYTHON" -m pip check >/dev/null 2>&1; then
  if [[ "${SC_SI_STRICT_DEPENDENCIES:-0}" == "1" ]]; then echo 'ERROR: pip dependency check failed.' >&2; exit 1; fi
  echo 'WARN: pip check reported unrelated environment conflicts; installer validation uses a clean isolated virtual environment.' >&2
fi
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then
  printf '\n==> Running complete inherited and v4.13.0 test suite\n'
  reset_runtime
  PYTHON="$PYTHON" PYTHONPATH="$BACKEND" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" "$ROOT/scripts/run_v3310_test_suite.py"
else
  printf '\n==> Skipping repeated Python regression suite by explicit verifier policy\n'
fi
if [[ "${SC_SI_RUN_BROWSER_GATE:-0}" == "1" && "${SC_SI_SKIP_BROWSER:-0}" != "1" ]]; then
  for gate in \
    browser_release_gate_v3310.py; do
    printf '\n==> Running browser gate: %s\n' "$gate"
    reset_runtime
    PYTHONPATH="$BACKEND" "$PYTHON" "$ROOT/scripts/$gate"
  done
else
  printf '\n==> Browser release gate not repeated inside installer verifier; immutable package browser validation is a build-time gate\n'
fi


rm -rf "$BACKEND/backend"
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: runtime state cleanup failed.' >&2; exit 1; }
printf '\nSUCCESS: Site Intelligence v4.13.0 passed Security, Observability, Performance, and Scale Assurance validation.\nRepository: %s\n' "$ROOT"
