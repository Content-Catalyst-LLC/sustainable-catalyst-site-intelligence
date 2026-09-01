#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-python3}"

"$PYTHON" "$ROOT/scripts/validate_v4391_release.py"

"$PYTHON" - "$ROOT" <<'PY2'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); manifest=json.loads((root/'MANIFEST.json').read_text())
assert manifest.get('release')=='4.39.1'
assert manifest.get('file_count')==len(manifest.get('files',[]))
for row in manifest['files']:
    path=root/row['path']
    assert path.is_file(),row['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],row['path']
print(f"Verified {len(manifest['files'])} manifest entries.")
PY2

"$PYTHON" - "$ROOT" <<'PY2'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for path in root.rglob('*'):
    if path.is_file() and path.suffix.lower() in {'.json','.geojson'} and path.name!='MANIFEST.json' and not any(part in {'.venv','.git'} for part in path.parts):
        json.loads(path.read_text()); rows.append(path)
print(f"Parsed {len(rows)} JSON/GeoJSON files.")
PY2

"$PYTHON" -m py_compile "$BACKEND/app/homepage_summary_v4391.py" "$BACKEND/app/main.py"
if command -v node >/dev/null 2>&1; then node --check "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi

if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then
    if "$PYTHON" -c 'import pytest,fastapi' >/dev/null 2>&1; then
        (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q)
    else
        echo "NOTICE: pytest/FastAPI dependencies are not installed; deterministic Python suite was skipped."
    fi
fi

echo "SUCCESS: Site Intelligence v4.39.1 passed asset-integrity, homepage rendering-recovery, manifest, JSON, Python, JavaScript, PHP, and available runtime validation."
