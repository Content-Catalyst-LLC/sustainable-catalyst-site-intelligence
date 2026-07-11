#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PLUGIN_FILE="$ROOT_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"

say() {
  printf '\n==> %s\n' "$*"
}

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

say "Validating required release files"
for required in README.md CHANGELOG.md LICENSE backend wordpress-plugin docs; do
  [[ -e "$ROOT_DIR/$required" ]] || fail "Missing required path: $required"
done

say "Checking canonical release markers"
grep -q 'APP_VERSION = "1.18.3"' "$BACKEND_DIR/app/version.py" || fail "Backend version marker is missing."
grep -q 'Version: 1.18.3' "$PLUGIN_FILE" || fail "WordPress plugin header version is missing."
grep -q "const VERSION = '1.18.3';" "$PLUGIN_FILE" || fail "WordPress plugin constant is missing."

say "Running Python tests"
TEMP_COUNTRY_CACHE="$(mktemp)"
rm -f "$TEMP_COUNTRY_CACHE"
(
  cd "$BACKEND_DIR"
  SC_SI_COUNTRY_CACHE_PATH="$TEMP_COUNTRY_CACHE" python3 -m pytest -q
)
rm -f "$TEMP_COUNTRY_CACHE" "${TEMP_COUNTRY_CACHE}.tmp"

say "Compiling Python"
(
  cd "$BACKEND_DIR"
  python3 -m compileall -q app
)

say "Checking standalone JavaScript"
if command -v node >/dev/null 2>&1; then
  node --check "$BACKEND_DIR/public_app/assets/app.js"
else
  printf 'Node is not installed; JavaScript syntax check skipped.\n'
fi

say "Checking WordPress PHP"
if command -v php >/dev/null 2>&1; then
  php -l "$PLUGIN_FILE"
else
  printf 'PHP is not installed; PHP syntax check skipped.\n'
fi

find "$ROOT_DIR" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
rm -f "$BACKEND_DIR/data/country_last_known_good.json" "$BACKEND_DIR/data/country_last_known_good.json.tmp"

say "Checking forbidden release artifacts"
# The root .git directory is expected in a normal checked-out repository.
# Nested repositories and generated dependency/cache directories remain
# forbidden release artifacts.
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

if find "$ROOT_DIR" -type f \( -name '.env' -o -name '*.pem' -o -name '*.key' -o -name 'country_last_known_good.json' -o -name 'platform_core_queue.jsonl' \) -print -quit | grep -q .; then
  find "$ROOT_DIR" -type f \( -name '.env' -o -name '*.pem' -o -name '*.key' -o -name 'country_last_known_good.json' -o -name 'platform_core_queue.jsonl' \) -print
  fail "Forbidden runtime or secret-bearing file found."
fi

say "Running private-key marker scan"
if grep -RIl --exclude-dir=.git --exclude='*.zip' --exclude='*.pdf' \
  -E 'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY' "$ROOT_DIR" | grep -q .; then
  grep -RIl --exclude-dir=.git --exclude='*.zip' --exclude='*.pdf' \
    -E 'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY' "$ROOT_DIR"
  fail "Private-key material detected."
fi

say "Release validation passed"
