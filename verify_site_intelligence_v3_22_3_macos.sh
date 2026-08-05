#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-}"

if [[ -z "$PYTHON" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON="$ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  else
    echo "ERROR: Python 3 is required." >&2
    exit 1
  fi
fi

printf '\n==> Verifying release identity\n'
grep -q 'APP_VERSION = "3.22.8"' "$BACKEND/app/version.py"
grep -q 'Version: 3.22.8' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'const RELEASE="3.22.8"' "$BACKEND/public_app/service-worker.js"
grep -q '/app/assets/service-recovery-v3224.js' "$BACKEND/public_app/index.html"
grep -q '/public/runtime-recovery' "$BACKEND/app/main.py"

printf '\n==> Verifying immutable repository manifest\n'
"$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1])
manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["release"] == "3.22.8"
assert manifest["file_count"] == len(manifest["files"])
for entry in manifest["files"]:
    path = root / entry["path"]
    data = path.read_bytes()
    assert len(data) == entry["bytes"], entry["path"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
print(f"Verified {len(manifest['files'])} manifest entries.")
PY

printf '\n==> Compiling Python modules\n'
"$PYTHON" -m compileall -q "$BACKEND/app" "$BACKEND/tests"

printf '\n==> Parsing JSON files\n'
"$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import json, sys
root = Path(sys.argv[1])
files = [path for path in root.rglob("*.json") if ".venv" not in path.parts]
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"Parsed {len(files)} JSON files.")
PY

if command -v node >/dev/null 2>&1; then
  printf '\n==> Checking JavaScript syntax\n'
  count=0
  while IFS= read -r -d '' file; do
    node --check "$file" >/dev/null
    count=$((count + 1))
  done < <(find "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)
  printf 'Validated %s JavaScript files.\n' "$count"
else
  echo "NOTE: Node.js not found; JavaScript syntax check skipped."
fi

if command -v php >/dev/null 2>&1; then
  printf '\n==> Checking WordPress PHP syntax\n'
  php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
else
  echo "NOTE: PHP not found; PHP syntax check skipped."
fi

printf '\n==> Running Site Intelligence tests\n'
cd "$BACKEND"
"$PYTHON" -m pytest -q

printf '\nSUCCESS: Site Intelligence v3.22.8 passed local validation.\n'
printf 'Repository: %s\n' "$ROOT"
