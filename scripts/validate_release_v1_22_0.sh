#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_TMP="$(mktemp -d "${TMPDIR:-/tmp}/site-intelligence-v1220-validation.XXXXXX")"
trap 'rm -rf "$VALIDATION_TMP"' EXIT

export PYTHONPYCACHEPREFIX="$VALIDATION_TMP/pycache"
export SC_SI_COUNTRY_CACHE_PATH="$VALIDATION_TMP/country_last_known_good.json"
export SC_SI_PLATFORM_CORE_QUEUE_PATH="$VALIDATION_TMP/platform_core_queue.jsonl"

say() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

say "Validating required release files"
for path in \
  README.md \
  CHANGELOG.md \
  backend/app/version.py \
  backend/app/source_methodology_studio.py \
  backend/tests/test_source_methodology_studio_v1220.py \
  backend/public_app/index.html \
  backend/public_app/assets/app.js \
  backend/public_app/assets/app.css \
  wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php \
  docs/SOURCE_AND_METHODOLOGY_STUDIO_V1220.md \
  docs/RELEASE_MANIFEST_V1220.json; do
  [[ -e "$ROOT_DIR/$path" ]] || fail "Missing required release path: $path"
done

say "Checking canonical release markers"
grep -q 'APP_VERSION = "1.22.0"' "$ROOT_DIR/backend/app/version.py" || fail "Backend version mismatch"
grep -q 'API_SCHEMA_VERSION = "1.22"' "$ROOT_DIR/backend/app/version.py" || fail "API schema version mismatch"
grep -q 'Version: 1.22.0' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin header mismatch"
grep -q "const VERSION = '1.22.0';" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin constant mismatch"
grep -q "add_shortcode('sc_source_methodology_studio'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Source studio shortcode registration missing"
grep -q 'public function source_methodology_studio_shortcode' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Source studio shortcode renderer missing"
grep -q '/public/source-methodology/diagnostics' "$ROOT_DIR/backend/app/main.py" || fail "Source methodology diagnostics endpoint missing"
grep -q '/public/source-methodology/export' "$ROOT_DIR/backend/app/main.py" || fail "Source methodology export endpoint missing"
grep -q 'data-route="sources"' "$ROOT_DIR/backend/public_app/index.html" || fail "Source studio app navigation missing"
grep -q 'id="sourceStudio"' "$ROOT_DIR/backend/public_app/index.html" || fail "Source studio app section missing"
grep -q 'openSourceStudio' "$ROOT_DIR/backend/public_app/assets/app.js" || fail "Source studio frontend controller missing"
grep -q 'world-bank' "$ROOT_DIR/docs/RELEASE_MANIFEST_V1220.json" || fail "Source release manifest missing required source IDs"
grep -Eq '^##[[:space:]]+1\.22\.0([[:space:]]|$)' "$ROOT_DIR/CHANGELOG.md" || fail "CHANGELOG does not contain the 1.22.0 release heading"

say "Running Python tests"
(
  cd "$ROOT_DIR/backend"
  python -m pytest -q -p no:cacheprovider
)

say "Compiling Python"
python -m compileall -q "$ROOT_DIR/backend/app"

say "Checking standalone JavaScript"
if command -v node >/dev/null 2>&1; then
  node --check "$ROOT_DIR/backend/public_app/assets/app.js"
fi

say "Checking WordPress JavaScript"
if command -v node >/dev/null 2>&1; then
  node --check "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js"
fi

say "Checking WordPress PHP"
if command -v php >/dev/null 2>&1; then
  php -l "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
fi

say "Checking CSS structure"
python - "$ROOT_DIR/backend/public_app/assets/app.css" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
if text.count("{") != text.count("}"):
    raise SystemExit("Unbalanced CSS braces")
print("CSS brace structure passed.")
PY

say "Checking forbidden release artifacts"
FORBIDDEN_DIRS="$(
  find "$ROOT_DIR" \
    -path "$ROOT_DIR/.git" -prune -o \
    -type d \( \
      -name .git -o \
      -name node_modules -o \
      -name __pycache__ -o \
      -name .pytest_cache -o \
      -name .venv -o \
      -name venv \
    \) -print
)"
if [[ -n "$FORBIDDEN_DIRS" ]]; then
  printf '%s\n' "$FORBIDDEN_DIRS"
  fail "Forbidden generated directory found."
fi

if find "$ROOT_DIR" -type f \( \
  -name '.env' -o \
  -name '*.pem' -o \
  -name '*.key' -o \
  -name '*.pyc' -o \
  -name 'country_last_known_good.json' -o \
  -name 'country_last_known_good.json.tmp' -o \
  -name 'platform_core_queue.jsonl' \
\) -print -quit | grep -q .; then
  fail "Forbidden runtime or secret-bearing file found."
fi

say "Checking private-key markers"
if grep -RIl --exclude='*.zip' --exclude='*.pdf' -E 'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY' "$ROOT_DIR" | grep -q .; then
  fail "Private-key material detected."
fi

say "Site Intelligence v1.22.0 validation passed"
