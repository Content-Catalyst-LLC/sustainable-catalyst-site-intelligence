#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
PYTHON="${PYTHON:-python3}"
"$PYTHON" "$ROOT/scripts/validate_v4380_release.py"
echo '==> Verifying immutable repository manifest'
"$PYTHON" - "$ROOT" <<'PY2'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'MANIFEST.json').read_text())
assert m.get('release')=='4.38.0'
assert m.get('file_count')==len(m.get('files',[]))
for row in m['files']:
 p=root/row['path']; assert p.is_file(),row['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print(f"Verified {len(m['files'])} manifest entries.")
PY2
echo '==> Parsing JSON/GeoJSON'
"$PYTHON" - "$ROOT" <<'PY2'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]
for p in root.rglob('*'):
 if p.is_file() and p.suffix.lower() in {'.json','.geojson'} and p.name!='MANIFEST.json' and not any(x in p.parts for x in ('.venv','.git')):
  json.loads(p.read_text()); rows.append(p)
print(f"Parsed {len(rows)} JSON/GeoJSON files.")
PY2
if command -v node >/dev/null 2>&1; then node "$ROOT/scripts/check_javascript_v43500.js" "$BACKEND/public_app" "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/assets"; fi
if command -v php >/dev/null 2>&1; then php -l "$ROOT/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"; fi
"$PYTHON" "$ROOT/scripts/security_static_scan_v41100.py" "$ROOT"
if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]]; then
  echo '==> Collecting deterministic pytest suite'
  COLLECTED="$(cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest --collect-only -q | sed -n 's/^\([0-9][0-9]*\) tests collected.*/\1/p' | tail -1)"
  [[ "$COLLECTED" == "1708" ]] || { echo "ERROR: expected 1708 collected tests, got ${COLLECTED:-unknown}" >&2; exit 1; }
  TEST_FILES=("$BACKEND"/tests/test_*.py); CHUNK_SIZE="${SC_SI_PYTEST_CHUNK_FILES:-57}"; OFFSET=0; CHUNK=1
  while (( OFFSET < ${#TEST_FILES[@]} )); do
    CURRENT=("${TEST_FILES[@]:OFFSET:CHUNK_SIZE}")
    printf '==> pytest chunk %s: files %s-%s of %s\n' "$CHUNK" "$((OFFSET+1))" "$((OFFSET+${#CURRENT[@]}))" "${#TEST_FILES[@]}"
    (cd "$BACKEND" && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PYTHON" -m pytest -q "${CURRENT[@]}")
    OFFSET=$((OFFSET+${#CURRENT[@]})); CHUNK=$((CHUNK+1))
  done
  printf 'PASS: all %s collected tests completed across deterministic chunks.\n' "$COLLECTED"
fi
if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then
  for script in browser_space_iframe_v4380.py browser_underwater_media_v4370.py browser_ocean_observation_v4360.py browser_science_ocean_workspace_controller_v4360_r4.py browser_palestine_navigation_integrity_v4360.py browser_country_evidence_presentation_v4360.py; do
    PYTHON="$PYTHON" PYTHONPATH="$BACKEND:$ROOT/scripts" "$PYTHON" "$ROOT/scripts/$script"
  done
  for mode in desktop mobile iframe; do PYTHON="$PYTHON" "$PYTHON" "$ROOT/scripts/browser_workspace_e2e_v4360.py" --mode "$mode"; done
fi
echo 'SUCCESS: Site Intelligence v4.38.0 passed five-lane live Space observation, iframe navigation, inherited live Underwater/Ocean, featured Ocean/Space, country/evidence, and 35-route platform validation.'
