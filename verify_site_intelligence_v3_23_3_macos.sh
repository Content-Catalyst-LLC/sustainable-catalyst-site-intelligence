#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3233-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
rm -rf "$BACKEND/backend"

printf '\n==> Verifying v3.23.6.4 release identity and source-truth contracts\n'
grep -q 'APP_VERSION = "3.23.6.4"' "$BACKEND/app/version.py"
grep -q 'Version: 3.23.6.4' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="3.23.6.4"' "$BACKEND/public_app/service-worker.js"
grep -q 'data-truth-v3233.js' "$BACKEND/public_app/index.html"
grep -q 'data-truth-v3233.css' "$BACKEND/public_app/index.html"
grep -q '/public/data-truth' "$BACKEND/app/main.py"
grep -q 'SCSIDataTruthV3233' "$BACKEND/public_app/assets/data-truth-v3233.js"
grep -q 'dataTruthJsUrl' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q "wp_enqueue_script('scsi-production-truth'" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q "wp_enqueue_script('scsi-cartographic-interaction'" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
! grep -q "wp_enqueue_script('scsi-data-truth'" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]); manifest=json.loads((root/'MANIFEST.json').read_text())
assert manifest['release']=='3.23.6.4'; assert manifest['file_count']==len(manifest['files'])
for entry in manifest['files']:
    path=root/entry['path']; data=path.read_bytes()
    assert len(data)==entry['bytes'],entry['path']
    assert hashlib.sha256(data).hexdigest()==entry['sha256'],entry['path']
print(f"Verified {len(manifest['files'])} manifest entries.")
PYVERIFY

printf '\n==> Compiling Python modules\n'
"$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests" "$ROOT/scripts"
printf '\n==> Parsing JSON and GeoJSON files\n'
"$PYTHON" - "$ROOT" <<'PYJSON'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]); files=[p for p in root.rglob('*') if p.is_file() and p.suffix in {'.json','.geojson'} and '.venv' not in p.parts and '.runtime' not in p.parts]
for path in files: json.loads(path.read_text())
print(f"Parsed {len(files)} JSON/GeoJSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then
  printf '\n==> Checking JavaScript syntax\n'; count=0
  while IFS= read -r -d '' file; do node --check "$file" >/dev/null; count=$((count+1)); done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)
  printf 'Validated %s JavaScript files.\n' "$count"
fi
if command -v php >/dev/null 2>&1; then
  printf '\n==> Checking WordPress PHP syntax\n'
  php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
fi
printf '\n==> Running all tests with adaptive process isolation\n'
PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/run_v3233_test_groups.py"
if [[ "${SC_SI_SKIP_BROWSER_SMOKE:-0}" != "1" ]]; then
  printf '\n==> Running Chromium smoke tests when available\n'
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3230.py"
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3231.py"
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3232.py"
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3233.py"
fi
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: tests wrote runtime state into the immutable checkout.' >&2; exit 1; }
printf '\nSUCCESS: Site Intelligence v3.23.6.4 passed deterministic validation.\nRepository: %s\n' "$ROOT"
