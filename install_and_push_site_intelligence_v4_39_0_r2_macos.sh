#!/usr/bin/env bash
set -euo pipefail

RELEASE="4.39.0"
REVISION="R2"
TAG="v4.39.0-r2"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$SCRIPT_ROOT"
REPO_DIR="${1:-$HOME/Downloads/sustainable-catalyst-site-intelligence}"

fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for command_name in git rsync python3 unzip; do
    command -v "$command_name" >/dev/null 2>&1 || fail "$command_name is required."
done

TEMP_ROOT=""
if [[ ! -f "$SOURCE_ROOT/backend/app/version.py" ]]; then
    REPOSITORY_ZIP="$SCRIPT_ROOT/sustainable-catalyst-site-intelligence-v4.39.0-r2-repository.zip"
    [[ -f "$REPOSITORY_ZIP" ]] || fail "The v4.39.0 R2 repository ZIP is missing beside this installer."
    TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v4390-r2.XXXXXX")"
    trap '[[ -n "$TEMP_ROOT" && -d "$TEMP_ROOT" ]] && rm -rf "$TEMP_ROOT"' EXIT
    unzip -q "$REPOSITORY_ZIP" -d "$TEMP_ROOT"
    SOURCE_ROOT="$TEMP_ROOT/sustainable-catalyst-site-intelligence-v4.39.0-r2"
    [[ -f "$SOURCE_ROOT/backend/app/version.py" ]] || fail "The repository ZIP has an unexpected structure."
fi

[[ -d "$REPO_DIR/.git" ]] || fail "$REPO_DIR is not an existing Git checkout."
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || fail "The target Git checkout has uncommitted changes. Commit or move them before installing v${RELEASE} ${REVISION}."

printf '\n==> Validating Site Intelligence v%s %s source\n' "$RELEASE" "$REVISION"
SC_SI_SKIP_TESTS=1 bash "$SOURCE_ROOT/verify_site_intelligence_v4_39_0_r2_macos.sh"

printf '\n==> Applying the certified compact capability revision to %s\n' "$REPO_DIR"
rsync -a \
  --exclude '.git/' --exclude '.venv/' --exclude '.pytest_cache/' \
  --exclude '__pycache__/' --exclude '*.pyc' \
  "$SOURCE_ROOT/" "$REPO_DIR/"

cd "$REPO_DIR"
git add -A
if git diff --cached --quiet; then
    echo "Site Intelligence v${RELEASE} ${REVISION} is already applied."
else
    git commit -m "Site Intelligence v${RELEASE} ${REVISION} — Compact Capability Console"
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
    [[ "$(git rev-list -n 1 "$TAG")" == "$(git rev-parse HEAD)" ]] || fail "Tag $TAG already points to another commit."
else
    git tag -a "$TAG" -m "Site Intelligence v${RELEASE} ${REVISION} — Compact Capability Console"
fi

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || fail "The Git checkout is in detached HEAD state."
git push origin "$BRANCH"
git push origin "$TAG"

printf '\nSUCCESS: Site Intelligence v%s %s was committed, tagged %s, and pushed to GitHub.\n' "$RELEASE" "$REVISION" "$TAG"
printf 'Deploy the backend container, replace the WordPress plugin, and install homepage v4.3.1.\n'
