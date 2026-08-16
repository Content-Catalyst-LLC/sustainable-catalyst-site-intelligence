#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-python3}"
EXPECTED_VERSION="4.36.1"
EXPECTED_TESTS="1684"

fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for c in "$PYTHON" grep shasum; do command -v "$c" >/dev/null 2>&1 || fail "$c is required"; done

echo "==> Checking release identity"
grep -q 'APP_VERSION = "4.36.1"' "$BACKEND/app/version.py"
grep -q 'Version: 4.36.1' "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
grep -q 'data-scsi-release="4.36.1"' "$BACKEND/public_app/index.html"
grep -q 'const RELEASE="4.36.1"' "$BACKEND/public_app/service-worker.js"

echo "==> Checking OpenAPI generation"
PYTHONPATH="$BACKEND" "$PYTHON" - <<'PY'
from app.main import app
schema = app.openapi()
assert schema["info"]["version"] == "4.36.1"
required = {
    "/public/authoritative-connectors/noaa-erddap/search",
    "/public/authoritative-connectors/noaa-coops/data",
    "/public/authoritative-connectors/obis/occurrences",
    "/public/authoritative-connectors/nasa-exoplanets",
    "/public/authoritative-connectors/nasa-cmr/collections",
}
missing = sorted(required - set(schema.get("paths", {})))
assert not missing, missing
print(f"PASS - OpenAPI generated with {len(schema.get('paths', {}))} paths")
PY

echo "==> Checking live-evidence browser bindings"
for marker in \
  '/public/authoritative-connectors/noaa-erddap/search' \
  '/public/authoritative-connectors/obis/occurrences' \
  '/public/authoritative-connectors/noaa-coops/data' \
  '/public/exoplanet-habitability/live' \
  '/public/authoritative-connectors/nasa-cmr/collections'; do
  grep -R -q "$marker" "$BACKEND/public_app/assets" || fail "Missing browser connector binding: $marker"
done

for asset in \
  ocean-surface-v4500 \
  marine-biodiversity-v4900 \
  coastal-change-v41400 \
  exoplanet-habitability-v43500 \
  planetary-intelligence-v4200; do
  cmp -s "$BACKEND/public_app/assets/${asset}.js" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.js" || fail "JS copy mismatch: $asset"
  cmp -s "$BACKEND/public_app/assets/${asset}.css" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/${asset}.css" || fail "CSS copy mismatch: $asset"
done

if command -v node >/dev/null 2>&1; then
  echo "==> Checking JavaScript syntax"
  for f in \
    "$BACKEND/public_app/assets/ocean-surface-v4500.js" \
    "$BACKEND/public_app/assets/marine-biodiversity-v4900.js" \
    "$BACKEND/public_app/assets/coastal-change-v41400.js" \
    "$BACKEND/public_app/assets/exoplanet-habitability-v43500.js" \
    "$BACKEND/public_app/assets/planetary-intelligence-v4200.js"; do
    node --check "$f"
  done
fi

if command -v php >/dev/null 2>&1; then
  echo "==> Checking WordPress PHP syntax"
  php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
fi

echo "==> Parsing JSON/GeoJSON"
"$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import json, sys
root=Path(sys.argv[1]); count=0
for p in root.rglob('*'):
    if not p.is_file() or p.name == 'MANIFEST.json' or p.suffix.lower() not in {'.json','.geojson'}:
        continue
    if any(part in {'.venv','.git','__pycache__'} for part in p.parts):
        continue
    json.loads(p.read_text())
    count += 1
print(f"PASS - parsed {count} JSON/GeoJSON files")
PY

if [[ -f "$ROOT/MANIFEST.json" ]]; then
  echo "==> Verifying immutable repository manifest"
  "$PYTHON" - "$ROOT" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
assert m.get('release') == '4.36.1', m.get('release')
for row in m.get('files', []):
    p=root/row['path']; assert p.is_file(), row['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'], row['path']
print(f"PASS - verified {len(m.get('files', []))} manifest entries")
PY
fi

if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then
  echo "==> Collecting deterministic pytest suite"
  COLLECTED="$(cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest --collect-only -q | sed -n 's/^\([0-9][0-9]*\) tests collected.*/\1/p' | tail -1)"
  [[ "$COLLECTED" == "$EXPECTED_TESTS" ]] || fail "expected $EXPECTED_TESTS collected tests, got ${COLLECTED:-unknown}"
  TEST_FILES=("$BACKEND"/tests/test_*.py)
  CHUNK_SIZE="${SC_SI_PYTEST_CHUNK_FILES:-55}"
  OFFSET=0; CHUNK=1
  while (( OFFSET < ${#TEST_FILES[@]} )); do
    CURRENT=("${TEST_FILES[@]:OFFSET:CHUNK_SIZE}")
    printf '==> pytest chunk %d: files %d-%d of %d\n' "$CHUNK" "$((OFFSET+1))" "$((OFFSET+${#CURRENT[@]}))" "${#TEST_FILES[@]}"
    (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q "${CURRENT[@]}")
    OFFSET=$((OFFSET+${#CURRENT[@]})); CHUNK=$((CHUNK+1))
  done
  echo "PASS - all $COLLECTED deterministic tests completed"
fi

if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then
  echo "==> Running deterministic v4.36.1 browser gate"
  PYTHONPATH="$BACKEND:$ROOT/scripts" "$PYTHON" "$ROOT/scripts/browser_live_evidence_v4361.py"
fi

echo
echo "SUCCESS: Site Intelligence v4.36.1 passed Ocean/Space live-evidence binding, OpenAPI recovery, asset parity, and inherited platform validation."
