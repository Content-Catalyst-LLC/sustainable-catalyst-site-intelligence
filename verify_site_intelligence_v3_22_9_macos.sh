#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  [[ -x "$ROOT/.venv/bin/python" ]] && PYTHON="$ROOT/.venv/bin/python" || PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" ]] || { echo "ERROR: Python 3 is required." >&2; exit 1; }
RUNTIME_SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3229-runtime.XXXXXX")"
trap 'rm -rf "$RUNTIME_SANDBOX" "$BACKEND/backend"' EXIT
export SC_SI_RUNTIME_STATE_ROOT="$RUNTIME_SANDBOX"
rm -rf "$BACKEND/backend"

printf '\n==> Verifying v3.22.9 release identity and production contracts\n'
grep -q 'APP_VERSION = "3.22.9"' "$BACKEND/app/version.py"
grep -q 'Version: 3.22.9' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="3.22.9"' "$BACKEND/public_app/service-worker.js"
grep -q 'vector-cartography-v3229.js' "$BACKEND/public_app/index.html"
grep -q 'world-cartography-v3229.geojson' "$BACKEND/public_app/service-worker.js"
grep -q 'networkFirstShell' "$BACKEND/public_app/service-worker.js"
grep -q 'expected_release_id' "$BACKEND/app/main.py"
grep -q 'SC_SI_RUNTIME_STATE_ROOT' "$ROOT/render.yaml"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PYVERIFY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]); manifest=json.loads((root/'MANIFEST.json').read_text())
assert manifest['release']=='3.22.9'; assert manifest['file_count']==len(manifest['files'])
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
printf '\n==> Running all tests in isolated deterministic shards\n'
SHARD_ARGS=(--python "$PYTHON" --shards 6 --timeout-seconds "${SC_SI_TEST_TIMEOUT_SECONDS:-12}")
if [[ -n "${SC_SI_VERIFY_ONLY_SHARD:-}" ]]; then SHARD_ARGS+=(--only-shard "$SC_SI_VERIFY_ONLY_SHARD"); fi
"$PYTHON" "$ROOT/scripts/run_test_shards_v3229.py" "${SHARD_ARGS[@]}"
if [[ "${SC_SI_SKIP_BROWSER_SMOKE:-0}" != "1" ]]; then
  printf '\n==> Running vector-cartography Chromium visual smoke test when available\n'
  "$PYTHON" "$ROOT/scripts/browser_smoke_v3229.py"
fi
[[ ! -e "$BACKEND/backend" ]] || { echo 'ERROR: tests wrote runtime state into the immutable checkout.' >&2; exit 1; }
printf '\nSUCCESS: Site Intelligence v3.22.9 passed deterministic validation.\nRepository: %s\nRuntime sandbox: isolated and removed on exit\n' "$ROOT"
