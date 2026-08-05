#!/usr/bin/env bash
set -euo pipefail

RELEASE="3.22.4"
REPO_SLUG="${SC_SI_GITHUB_REPOSITORY:-Content-Catalyst-LLC/sustainable-catalyst-site-intelligence}"
RENDER_URL="${SC_SI_RENDER_URL:-https://sustainable-catalyst-site-intelligence.onrender.com}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SC_SI_DEPLOY_ROOT:-$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy}"
CLONE_ROOT="$DEPLOY_ROOT/repository"
BRANCH=""

fail() {
  printf '\nERROR: %s\n' "$1" >&2
  exit 1
}

for command in git curl python3 rsync; do
  command -v "$command" >/dev/null 2>&1 || fail "$command is required."
done

printf '\n==> Validating release source before promotion\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$SOURCE_ROOT/verify_site_intelligence_v3_22_4_macos.sh"
else
  bash "$SOURCE_ROOT/verify_site_intelligence_v3_22_4_macos.sh"
fi

printf '\n==> Preparing a clean GitHub deployment clone\n'
rm -rf "$DEPLOY_ROOT"
mkdir -p "$DEPLOY_ROOT"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh repo clone "$REPO_SLUG" "$CLONE_ROOT" -- --quiet
else
  git clone --quiet "git@github.com:${REPO_SLUG}.git" "$CLONE_ROOT" \
    || fail "GitHub clone failed. Confirm GitHub CLI authentication or SSH access for $REPO_SLUG."
fi

git -C "$CLONE_ROOT" remote set-head origin -a >/dev/null 2>&1 || true
BRANCH="$(git -C "$CLONE_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
if [[ -z "$BRANCH" ]]; then
  BRANCH="main"
fi

git -C "$CLONE_ROOT" checkout "$BRANCH" >/dev/null 2>&1
git -C "$CLONE_ROOT" pull --ff-only origin "$BRANCH"

printf '\n==> Synchronizing v%s into %s/%s\n' "$RELEASE" "$REPO_SLUG" "$BRANCH"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$SOURCE_ROOT/" "$CLONE_ROOT/"

printf '\n==> Revalidating the exact Git tree that will be pushed\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$CLONE_ROOT/verify_site_intelligence_v3_22_4_macos.sh"
else
  bash "$CLONE_ROOT/verify_site_intelligence_v3_22_4_macos.sh"
fi

cd "$CLONE_ROOT"
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A

if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail "Git user.name is not configured. Run: git config --global user.name \"Your Name\""
  git config user.email >/dev/null 2>&1 || fail "Git user.email is not configured. Run: git config --global user.email \"you@example.com\""
  git commit -m "Site Intelligence v${RELEASE} — Render deployment parity and release promotion"
else
  printf 'No uncommitted release differences were found; using the current branch head.\n'
fi

COMMIT="$(git rev-parse HEAD)"
CURRENT_VERSION="$(python3 - <<'PY'
from pathlib import Path
import re
text=Path('backend/app/version.py').read_text(encoding='utf-8')
match=re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
print(match.group(1) if match else '')
PY
)"
[[ "$CURRENT_VERSION" == "$RELEASE" ]] || fail "Deployment tree reports v$CURRENT_VERSION instead of v$RELEASE."

if git rev-parse "refs/tags/v${RELEASE}" >/dev/null 2>&1; then
  TAG_COMMIT="$(git rev-list -n 1 "v${RELEASE}")"
  [[ "$TAG_COMMIT" == "$COMMIT" ]] || fail "Tag v${RELEASE} already points to a different commit."
else
  git tag -a "v${RELEASE}" -m "Site Intelligence v${RELEASE}"
fi

printf '\n==> Pushing backend release commit %s\n' "${COMMIT:0:12}"
git push origin "$BRANCH"
git push origin "v${RELEASE}"

TRIGGERED="auto-deploy"
if [[ -n "${SC_SI_RENDER_DEPLOY_HOOK:-}" ]]; then
  separator='?'
  [[ "$SC_SI_RENDER_DEPLOY_HOOK" == *'?'* ]] && separator='&'
  curl -fsS -X POST "${SC_SI_RENDER_DEPLOY_HOOK}${separator}ref=${COMMIT}" >/dev/null
  TRIGGERED="deploy-hook"
elif command -v render >/dev/null 2>&1 && render whoami >/dev/null 2>&1; then
  render deploys create "${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence}" \
    --commit "$COMMIT" --clear-cache --wait
  TRIGGERED="render-cli"
fi

printf '\n==> Verifying the live Render backend\n'
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-80}"
INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-15}"
OBSERVED_VERSION="unavailable"
OBSERVED_COMMIT="unavailable"

for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  payload="$(curl -fsS --max-time 45 "${RENDER_URL%/}/public/build-info?release_check=${RELEASE}-${attempt}" 2>/dev/null || true)"
  if [[ -n "$payload" ]]; then
    read -r OBSERVED_VERSION OBSERVED_COMMIT < <(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("backend_version",d.get("version","unavailable")), d.get("git_commit","unavailable"))' <<<"$payload" 2>/dev/null || printf 'unavailable unavailable\n')
    if [[ "$OBSERVED_VERSION" == "$RELEASE" && ( "$OBSERVED_COMMIT" == "$COMMIT" || "$COMMIT" == "$OBSERVED_COMMIT"* || "$OBSERVED_COMMIT" == "$COMMIT"* ) ]]; then
      printf 'Render reports v%s at commit %s.\n' "$OBSERVED_VERSION" "${OBSERVED_COMMIT:0:12}"
      printf '\nSUCCESS: GitHub and Render are synchronized for Site Intelligence v%s.\n' "$RELEASE"
      printf 'GitHub repository: https://github.com/%s\n' "$REPO_SLUG"
      printf 'Render backend: %s\n' "$RENDER_URL"
      printf 'Deployment trigger: %s\n' "$TRIGGERED"
      exit 0
    fi
  fi
  sleep "$INTERVAL"
done

cat >&2 <<EOF

ERROR: GitHub was updated, but Render did not reach the pushed release.
Expected version: $RELEASE
Expected commit:  $COMMIT
Observed version: $OBSERVED_VERSION
Observed commit:  $OBSERVED_COMMIT

Open Render -> sustainable-catalyst-site-intelligence -> Settings and confirm:
  Branch: $BRANCH
  Auto-Deploy: On Commit

Then use Manual Deploy -> Clear build cache & deploy.
The required commit is $COMMIT.
Do not update the WordPress plugin until /public/build-info reports v$RELEASE and this commit.
EOF
exit 1
