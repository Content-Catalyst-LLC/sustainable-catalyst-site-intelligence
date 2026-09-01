#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> v4.39.2 surgical preservation gate"
python3 scripts/validate_v4392_surgical_scope.py

echo "==> v4.39.2 release contract"
python3 scripts/validate_v4392_release_contract.py

echo "==> Python syntax"
python3 -m py_compile backend/app/version.py scripts/validate_v4392_surgical_scope.py scripts/validate_v4392_release_contract.py

if command -v node >/dev/null 2>&1; then
  echo "==> JavaScript syntax"
  node --check wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js
else
  echo "SKIP - node unavailable"
fi

if command -v php >/dev/null 2>&1; then
  echo "==> WordPress PHP syntax"
  php -l wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php
else
  echo "SKIP - php unavailable"
fi

if [[ "${SC_SI_SKIP_TESTS:-0}" != "1" ]] && command -v pytest >/dev/null 2>&1; then
  echo "==> Targeted backend regression"
  (cd backend && PYTHONPATH=. pytest -q tests/test_homepage_summary_v4390.py tests/test_live_intelligence_frontend_recovery_v4392.py)
else
  echo "SKIP - targeted pytest (SC_SI_SKIP_TESTS=1 or pytest unavailable)"
fi

echo "PASS - Site Intelligence v4.39.2 verification"
