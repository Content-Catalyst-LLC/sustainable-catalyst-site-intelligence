#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_TMP="$(mktemp -d "${TMPDIR:-/tmp}/site-intelligence-v200-validation.XXXXXX")"
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
  backend/app/auditable_public_observatory.py \
  backend/tests/test_auditable_public_observatory_v200.py \
  backend/public_app/index.html \
  backend/public_app/assets/app.js \
  backend/public_app/assets/app.css \
  wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php \
  docs/AUDITABLE_PUBLIC_OBSERVATORY_V200.md \
  docs/RELEASE_MANIFEST_V200.json; do
  [[ -e "$ROOT_DIR/$path" ]] || fail "Missing required release path: $path"
done

say "Checking canonical release markers"
grep -q 'APP_VERSION = "2.0.0"' "$ROOT_DIR/backend/app/version.py" || fail "Backend version mismatch"
grep -q 'API_SCHEMA_VERSION = "2.0"' "$ROOT_DIR/backend/app/version.py" || fail "API schema version mismatch"
grep -q 'RELEASE_NAME = "Auditable Public Observatory"' "$ROOT_DIR/backend/app/version.py" || fail "Release name mismatch"
grep -q 'Version: 2.0.0' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin header mismatch"
grep -q "const VERSION = '2.0.0';" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin constant mismatch"
grep -q "add_shortcode('sc_auditable_public_observatory'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Observatory shortcode registration missing"
grep -q 'public function auditable_public_observatory_shortcode' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Observatory shortcode renderer missing"
grep -q "LEGACY_SHORTCODE_REMOVAL_TARGET = 'fulfilled-in-2.0.0'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Legacy transition marker missing"
grep -q "LEGACY_SHORTCODE_COMPATIBILITY = 'modern-workspace-aliases'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Legacy compatibility marker missing"
grep -q '/public/observatory/catalog' "$ROOT_DIR/backend/app/main.py" || fail "Observatory catalog endpoint missing"
grep -q '/public/observatory/audit/{artifact_id}' "$ROOT_DIR/backend/app/main.py" || fail "Observatory audit record endpoint missing"
grep -q '/public/observatory/lineage' "$ROOT_DIR/backend/app/main.py" || fail "Observatory lineage endpoint missing"
grep -q '/public/observatory/verify' "$ROOT_DIR/backend/app/main.py" || fail "Observatory verification endpoint missing"
grep -q '/public/observatory/release-ledger' "$ROOT_DIR/backend/app/main.py" || fail "Observatory release ledger endpoint missing"
grep -q '/public/observatory/diagnostics' "$ROOT_DIR/backend/app/main.py" || fail "Observatory diagnostics endpoint missing"
grep -q '/public/observatory/export' "$ROOT_DIR/backend/app/main.py" || fail "Observatory export endpoint missing"
grep -q 'data-route="observatory"' "$ROOT_DIR/backend/public_app/index.html" || fail "Observatory navigation missing"
grep -q 'id="auditablePublicObservatory"' "$ROOT_DIR/backend/public_app/index.html" || fail "Observatory workspace missing"
grep -q 'openAuditablePublicObservatory' "$ROOT_DIR/backend/public_app/assets/app.js" || fail "Observatory route loader missing"
grep -q 'auditable-observatory' "$ROOT_DIR/backend/public_app/assets/app.css" || fail "Observatory styling missing"
grep -q 'sc-auditable-public-observatory/2.0' "$ROOT_DIR/docs/RELEASE_MANIFEST_V200.json" || fail "Observatory schema marker missing"
grep -Eq '^##[[:space:]]+2\.0\.0([[:space:]]|$)' "$ROOT_DIR/CHANGELOG.md" || fail "CHANGELOG does not contain the 2.0.0 release heading"

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

say "Checking CSS structure and first-party budget"
python - "$ROOT_DIR/backend/public_app/assets/app.css" <<'PY2'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if text.count("{") != text.count("}"):
    raise SystemExit("Unbalanced CSS braces")
if path.stat().st_size > 100_000:
    raise SystemExit("First-party CSS exceeds the 100,000-byte release budget")
print("CSS brace structure and byte budget passed.")
PY2

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

say "Site Intelligence v2.0.0 validation passed"
