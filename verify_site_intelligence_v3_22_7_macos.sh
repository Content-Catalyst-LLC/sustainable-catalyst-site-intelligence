#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3227-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
rm -rf "$BACKEND/backend"
printf '
==> Verifying release identity and deployment contracts
'
grep -q 'APP_VERSION = "3.22.7"' "$BACKEND/app/version.py"
grep -q 'Version: 3.22.7' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="3.22.7"' "$BACKEND/public_app/service-worker.js"
grep -q '/public/deployment-receipt' "$BACKEND/app/main.py"
grep -q 'expected_release_id' "$BACKEND/app/main.py"
grep -q 'SC_SI_RUNTIME_STATE_ROOT' "$ROOT/render.yaml"
grep -q 'DEPLOYMENT_RECEIPT=' "$ROOT/promote_site_intelligence_v3_22_7_to_github_and_render_macos.sh"
printf '
==> Verifying immutable repository manifest
'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1]); manifest=json.loads((root/'MANIFEST.json').read_text())
assert manifest['release']=='3.22.7'; assert manifest['file_count']==len(manifest['files'])
for e in manifest['files']:
    p=root/e['path']; data=p.read_bytes()
    assert len(data)==e['bytes'],e['path']
    assert hashlib.sha256(data).hexdigest()==e['sha256'],e['path']
print(f"Verified {len(manifest['files'])} manifest entries.")
PYVERIFY
printf '
==> Compiling Python modules
'
"$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests"
printf '
==> Parsing JSON files
'
"$PYTHON" - "$ROOT" <<'PYJSON'
from pathlib import Path
import json,sys
root=Path(sys.argv[1]); files=[p for p in root.rglob('*.json') if '.venv' not in p.parts and '.runtime' not in p.parts]
for p in files: json.loads(p.read_text())
print(f"Parsed {len(files)} JSON files.")
PYJSON
if command -v node >/dev/null 2>&1; then
  printf '
==> Checking JavaScript syntax
'; count=0
  while IFS= read -r -d '' file; do node --check "$file" >/dev/null; count=$((count+1)); done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)
  printf 'Validated %s JavaScript files.
' "$count"
fi
if command -v php >/dev/null 2>&1; then
  printf '
==> Checking WordPress PHP syntax
'
  php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
fi
printf '
==> Running Site Intelligence tests in isolated runtime state
'
(cd "$BACKEND" && "$PYTHON" -m pytest -q)
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: tests wrote runtime state into the immutable checkout.' >&2; exit 1; }
printf '
SUCCESS: Site Intelligence v3.22.7 passed deterministic local validation.
Repository: %s
Runtime sandbox: isolated and removed on exit
' "$ROOT"
