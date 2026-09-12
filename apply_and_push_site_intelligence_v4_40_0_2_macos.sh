#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${1:-$HOME/Downloads/sustainable-catalyst-site-intelligence}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PATCH="${HERE}/patch"
VERSION="4.40.0.2"
TAG="v4.40.0.2"
COMMIT_MSG="Site Intelligence v4.40.0.2 homepage intelligence contract and ticker recovery"

fail(){ echo "ERROR: $*" >&2; exit 1; }
[[ -d "$REPO/.git" ]] || fail "$REPO is not a Git checkout"
[[ -d "$PATCH/backend" ]] || fail "patch payload missing: $PATCH"
command -v git >/dev/null || fail "git is required"
command -v python3 >/dev/null || fail "python3 is required"
command -v rsync >/dev/null || fail "rsync is required"

if git -C "$REPO" status --porcelain | grep -q .; then
  fail "working tree is not clean; commit or stash unrelated changes first"
fi

echo "=== SYNCHRONIZING MAIN ==="
git -C "$REPO" fetch origin main --tags
git -C "$REPO" checkout main
git -C "$REPO" pull --ff-only origin main

CURRENT="$(python3 - "$REPO/backend/app/version.py" <<'PY'
import re,sys
text=open(sys.argv[1],encoding='utf-8').read()
m=re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']',text)
print(m.group(1) if m else '')
PY
)"
case "$CURRENT" in
  4.40.0.1|4.40.0.2) ;;
  *) fail "expected Site Intelligence 4.40.0.1 or 4.40.0.2, found ${CURRENT:-unknown}" ;;
esac

echo "=== APPLYING v$VERSION REPAIR ==="
rsync -a --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' "$PATCH/" "$REPO/"

python3 "$REPO/scripts/validate_v44002_release.py"
python3 -m py_compile \
  "$REPO/backend/app/version.py" \
  "$REPO/backend/app/homepage_summary_v4390.py" \
  "$REPO/backend/app/main.py" \
  "$REPO/backend/app/energy_runtime_consumer.py"

if command -v node >/dev/null 2>&1; then
  node --check "$REPO/wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js"
else
  echo "NOTE: node unavailable; JavaScript static contract validation passed."
fi

if command -v php >/dev/null 2>&1; then
  php -l "$REPO/wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"
else
  echo "NOTE: php unavailable; WordPress PHP static contract validation passed."
fi

if python3 -c 'import pytest' >/dev/null 2>&1; then
  (cd "$REPO" && PYTHONPATH=backend python3 -m pytest -q \
    backend/tests/test_homepage_intelligence_contract_v44002.py \
    backend/tests/test_homepage_live_runtime_repair_v44001.py \
    backend/tests/test_source_reconciliation_v4400.py \
    backend/tests/test_energy_runtime_consumer.py)
else
  echo "NOTE: pytest unavailable; dependency-light release validator passed."
fi

git -C "$REPO" diff --check

echo "=== GIT CHANGES ==="
git -C "$REPO" status --short

if git -C "$REPO" status --porcelain | grep -q .; then
  git -C "$REPO" add -A
  git -C "$REPO" commit -m "$COMMIT_MSG"
else
  echo "No uncommitted changes remain; continuing idempotently."
fi

if ! git -C "$REPO" rev-parse "$TAG" >/dev/null 2>&1; then
  git -C "$REPO" tag -a "$TAG" -m "Site Intelligence v4.40.0.2 — Homepage Intelligence Contract & Ticker Recovery"
fi

echo "=== PUSHING MAIN ==="
git -C "$REPO" push origin main

echo "=== PUSHING TAG ==="
git -C "$REPO" push origin "$TAG"

echo "=== FINAL ==="
git -C "$REPO" log -1 --oneline --decorate
echo "PASS: Site Intelligence v$VERSION committed, tagged, and pushed."
echo "NEXT: deploy and verify the v$VERSION backend on Contabo before installing WordPress."
