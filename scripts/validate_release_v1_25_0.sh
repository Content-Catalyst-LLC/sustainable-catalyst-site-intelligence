#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_TMP="$(mktemp -d "${TMPDIR:-/tmp}/site-intelligence-v1250-validation.XXXXXX")"
trap 'rm -rf "$VALIDATION_TMP"' EXIT

export PYTHONPYCACHEPREFIX="$VALIDATION_TMP/pycache"
export SC_SI_COUNTRY_CACHE_PATH="$VALIDATION_TMP/country_last_known_good.json"
export SC_SI_PLATFORM_CORE_QUEUE_PATH="$VALIDATION_TMP/platform_core_queue.jsonl"

say() { printf '
==> %s
' "$*"; }
fail() { printf '
ERROR: %s
' "$*" >&2; exit 1; }

say "Validating required release files"
for path in   README.md   CHANGELOG.md   backend/app/version.py   backend/app/public_launch_portfolio.py   backend/tests/test_public_launch_portfolio_v1250.py   backend/public_app/index.html   backend/public_app/assets/app.js   backend/public_app/assets/app.css   wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php   docs/PUBLIC_LAUNCH_PORTFOLIO_V1250.md   docs/LAUNCH_MATERIALS_V1250.md   docs/RELEASE_MANIFEST_V1250.json; do
  [[ -e "$ROOT_DIR/$path" ]] || fail "Missing required release path: $path"
done

say "Checking canonical release markers"
grep -q 'APP_VERSION = "1.25.0"' "$ROOT_DIR/backend/app/version.py" || fail "Backend version mismatch"
grep -q 'API_SCHEMA_VERSION = "1.25"' "$ROOT_DIR/backend/app/version.py" || fail "API schema version mismatch"
grep -q 'Version: 1.25.0' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin header mismatch"
grep -q "const VERSION = '1.25.0';" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Plugin constant mismatch"
grep -q "add_shortcode('sc_site_intelligence_launch'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Launch shortcode registration missing"
grep -q 'public function site_intelligence_launch_shortcode' "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Launch shortcode renderer missing"
grep -q "LEGACY_SHORTCODE_REMOVAL_TARGET = '2.0.0'" "$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php" || fail "Legacy shortcode removal target missing"
grep -q '/public/launch-profile/materials' "$ROOT_DIR/backend/app/main.py" || fail "Launch materials endpoint missing"
grep -q '/public/launch-profile/diagnostics' "$ROOT_DIR/backend/app/main.py" || fail "Launch diagnostics endpoint missing"
grep -q '/public/launch-profile/portfolio' "$ROOT_DIR/backend/app/main.py" || fail "Portfolio endpoint missing"
grep -q 'data-route="launch"' "$ROOT_DIR/backend/public_app/index.html" || fail "Launch app navigation missing"
grep -q 'id="publicLaunchPortfolio"' "$ROOT_DIR/backend/public_app/index.html" || fail "Launch portfolio section missing"
grep -q 'openPublicLaunchPortfolio' "$ROOT_DIR/backend/public_app/assets/app.js" || fail "Launch route loader missing"
grep -q 'public-launch-portfolio' "$ROOT_DIR/backend/public_app/assets/app.css" || fail "Launch portfolio styling missing"
grep -q 'sc-site-intelligence-launch/1.0' "$ROOT_DIR/docs/RELEASE_MANIFEST_V1250.json" || fail "Launch profile schema missing"
grep -Eq '^##[[:space:]]+1\.25\.0([[:space:]]|$)' "$ROOT_DIR/CHANGELOG.md" || fail "CHANGELOG does not contain the 1.25.0 release heading"

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
python - "$ROOT_DIR/backend/public_app/assets/app.css" <<'PY2'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
if text.count("{") != text.count("}"):
    raise SystemExit("Unbalanced CSS braces")
print("CSS brace structure passed.")
PY2

say "Checking forbidden release artifacts"
FORBIDDEN_DIRS="$(
  find "$ROOT_DIR"     -path "$ROOT_DIR/.git" -prune -o     -type d \(       -name .git -o       -name node_modules -o       -name __pycache__ -o       -name .pytest_cache -o       -name .venv -o       -name venv     \) -print
)"
if [[ -n "$FORBIDDEN_DIRS" ]]; then
  printf '%s
' "$FORBIDDEN_DIRS"
  fail "Forbidden generated directory found."
fi

if find "$ROOT_DIR" -type f \(   -name '.env' -o   -name '*.pem' -o   -name '*.key' -o   -name '*.pyc' -o   -name 'country_last_known_good.json' -o   -name 'country_last_known_good.json.tmp' -o   -name 'platform_core_queue.jsonl' \) -print -quit | grep -q .; then
  fail "Forbidden runtime or secret-bearing file found."
fi

say "Checking private-key markers"
if grep -RIl --exclude='*.zip' --exclude='*.pdf' -E 'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY' "$ROOT_DIR" | grep -q .; then
  fail "Private-key material detected."
fi

say "Site Intelligence v1.25.0 validation passed"
