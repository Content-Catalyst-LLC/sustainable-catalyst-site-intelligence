#!/usr/bin/env bash
set -euo pipefail

RELEASE="3.22.5"
REPO_SLUG="${SC_SI_GITHUB_REPOSITORY:-Content-Catalyst-LLC/sustainable-catalyst-site-intelligence}"
RENDER_URL="${SC_SI_RENDER_URL:-https://sustainable-catalyst-site-intelligence.onrender.com}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SC_SI_DEPLOY_ROOT:-$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy}"
CLONE_ROOT="$DEPLOY_ROOT/repository"
BRANCH=""

fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

for command in git curl python3 rsync; do
  command -v "$command" >/dev/null 2>&1 || fail "$command is required."
done

printf '\n==> Validating release source before promotion\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$SOURCE_ROOT/verify_site_intelligence_v3_22_5_macos.sh"
else
  bash "$SOURCE_ROOT/verify_site_intelligence_v3_22_5_macos.sh"
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
[[ -n "$BRANCH" ]] || BRANCH="main"
git -C "$CLONE_ROOT" checkout "$BRANCH" >/dev/null 2>&1
git -C "$CLONE_ROOT" pull --ff-only origin "$BRANCH"

PREVIOUS_COMMIT="$(git -C "$CLONE_ROOT" rev-parse HEAD)"
ROLLBACK_TAG="site-intelligence-pre-v${RELEASE}-${PREVIOUS_COMMIT:0:12}"
if ! git -C "$CLONE_ROOT" rev-parse "refs/tags/$ROLLBACK_TAG" >/dev/null 2>&1; then
  git -C "$CLONE_ROOT" tag -a "$ROLLBACK_TAG" "$PREVIOUS_COMMIT" -m "Rollback point before Site Intelligence v${RELEASE}"
fi

printf '\n==> Synchronizing v%s into %s/%s\n' "$RELEASE" "$REPO_SLUG" "$BRANCH"
rsync -a --delete \
  --exclude '.git/' --exclude '.venv/' --exclude '.pytest_cache/' \
  --exclude '__pycache__/' --exclude '*.pyc' \
  "$SOURCE_ROOT/" "$CLONE_ROOT/"

printf '\n==> Revalidating the exact Git tree that will be pushed\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$CLONE_ROOT/verify_site_intelligence_v3_22_5_macos.sh"
else
  bash "$CLONE_ROOT/verify_site_intelligence_v3_22_5_macos.sh"
fi

cd "$CLONE_ROOT"
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — deployment gate and rollback readiness"
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
  [[ "$(git rev-list -n 1 "v${RELEASE}")" == "$COMMIT" ]] || fail "Tag v${RELEASE} already points to a different commit."
else
  git tag -a "v${RELEASE}" -m "Site Intelligence v${RELEASE}"
fi

printf '\n==> Pushing rollback point, release commit, and tag\n'
git push origin "$ROLLBACK_TAG"
git push origin "$BRANCH"
git push origin "v${RELEASE}"

TRIGGERED="auto-deploy"
if [[ -n "${SC_SI_RENDER_DEPLOY_HOOK:-}" ]]; then
  separator='?'; [[ "$SC_SI_RENDER_DEPLOY_HOOK" == *'?'* ]] && separator='&'
  curl -fsS -X POST "${SC_SI_RENDER_DEPLOY_HOOK}${separator}ref=${COMMIT}" >/dev/null
  TRIGGERED="deploy-hook"
elif command -v render >/dev/null 2>&1 && render whoami >/dev/null 2>&1; then
  render deploys create "${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence}" \
    --commit "$COMMIT" --clear-cache --wait
  TRIGGERED="render-cli"
fi

printf '\n==> Verifying the live Render release gate\n'
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-80}"
INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-15}"
OBSERVED_VERSION="unavailable"; OBSERVED_COMMIT="unavailable"; OBSERVED_GATE="unavailable"
for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  endpoint="${RENDER_URL%/}/public/release-gate?plugin_version=${RELEASE}&expected_commit=${COMMIT}&cache_bust=${attempt}"
  payload="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Pragma: no-cache' "$endpoint" 2>/dev/null || true)"
  if [[ -n "$payload" ]]; then
    read -r OBSERVED_VERSION OBSERVED_COMMIT OBSERVED_GATE < <(python3 -c 'import json,sys; d=json.load(sys.stdin); dep=d.get("deployment",{}); print(d.get("backend_version",d.get("version","unavailable")), dep.get("git_commit",d.get("git_commit","unavailable")), "ready" if d.get("install_allowed") else d.get("gate_state","blocked"))' <<<"$payload" 2>/dev/null || printf 'unavailable unavailable unavailable\n')
    if [[ "$OBSERVED_VERSION" == "$RELEASE" && "$OBSERVED_GATE" == "ready" && ( "$OBSERVED_COMMIT" == "$COMMIT" || "$COMMIT" == "$OBSERVED_COMMIT"* || "$OBSERVED_COMMIT" == "$COMMIT"* ) ]]; then
      printf 'Render release gate is ready for v%s at commit %s.\n' "$OBSERVED_VERSION" "${OBSERVED_COMMIT:0:12}"
      printf '\nSUCCESS: GitHub, Render, and the WordPress installation gate are synchronized.\n'
      printf 'Deployment trigger: %s\n' "$TRIGGERED"
      printf 'Rollback tag: %s (%s)\n' "$ROLLBACK_TAG" "${PREVIOUS_COMMIT:0:12}"
      printf 'Render rollback command: render deploys create %s --commit %s --wait\n' "${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence}" "$PREVIOUS_COMMIT"
      exit 0
    fi
  fi
  sleep "$INTERVAL"
done

cat >&2 <<EOF

ERROR: GitHub was updated, but the Render release gate did not become ready.
Expected version: $RELEASE
Expected commit:  $COMMIT
Observed version: $OBSERVED_VERSION
Observed commit:  $OBSERVED_COMMIT
Observed gate:    $OBSERVED_GATE
Rollback tag:    $ROLLBACK_TAG
Previous commit: $PREVIOUS_COMMIT

Use Render -> Manual Deploy -> Clear build cache & deploy for commit $COMMIT.
Do not install the WordPress ZIP until /public/release-gate reports install_allowed=true.
To restore the previous backend with Render CLI:
  render deploys create ${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence} --commit $PREVIOUS_COMMIT --wait
EOF
exit 1
