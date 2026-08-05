#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$SCRIPT_DIR"

if [[ ! -f "$REPO_DIR/backend/app/version.py" ]]; then
  echo "ERROR: Run this script from the extracted v3.22.1 repository folder."
  exit 1
fi

echo "==> Static release contract"
python3 "$REPO_DIR/scripts/validate_v3221_release.py"

echo "==> JavaScript syntax"
while IFS= read -r -d '' file; do node --check "$file" >/dev/null; done < <(find "$REPO_DIR/backend/public_app/assets" "$REPO_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/assets" -type f -name '*.js' -print0)

echo "==> WordPress PHP syntax"
php -l "$REPO_DIR/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"

echo "==> Python test suite"
cd "$REPO_DIR/backend"
PYTHONPATH=. python3 -m pytest -q

echo "SUCCESS: Site Intelligence v3.22.1 validation passed."
