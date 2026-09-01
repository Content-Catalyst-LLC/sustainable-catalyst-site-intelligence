#!/usr/bin/env bash
set -euo pipefail

RELEASE="4.39.0"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$SCRIPT_ROOT"
REPO_DIR="${1:-$HOME/Downloads/sustainable-catalyst-site-intelligence}"

fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for command_name in git rsync python3 unzip; do command -v "$command_name" >/dev/null 2>&1 || fail "$command_name is required."; done

TEMP_ROOT=""
if [[ ! -f "$SOURCE_ROOT/backend/app/version.py" ]]; then
    REPOSITORY_ZIP="$SCRIPT_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"
    [[ -f "$REPOSITORY_ZIP" ]] || fail "The v${RELEASE} repository ZIP is missing beside this installer."
    TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/scsi-v4390.XXXXXX")"
    trap '[[ -n "$TEMP_ROOT" && -d "$TEMP_ROOT" ]] && rm -rf "$TEMP_ROOT"' EXIT
    unzip -q "$REPOSITORY_ZIP" -d "$TEMP_ROOT"
    SOURCE_ROOT="$TEMP_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}"
    [[ -f "$SOURCE_ROOT/backend/app/version.py" ]] || fail "The repository ZIP has an unexpected structure."
fi
[[ -d "$REPO_DIR/.git" ]] || fail "$REPO_DIR is not an existing Git checkout."
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || fail "The target Git checkout has uncommitted changes. Commit or move them before installing v${RELEASE}."

printf '\n==> Validating Site Intelligence v%s source\n' "$RELEASE"
SC_SI_SKIP_TESTS=1 bash "$SOURCE_ROOT/verify_site_intelligence_v4_39_0_macos.sh"

printf '\n==> Applying the certified release to %s\n' "$REPO_DIR"
rsync -a --delete \
  --exclude '.git/' --exclude '.venv/' --exclude '.pytest_cache/' \
  --exclude '__pycache__/' --exclude '*.pyc' \
  "$SOURCE_ROOT/" "$REPO_DIR/"

cd "$REPO_DIR"
git add -A
if git diff --cached --quiet; then
    echo "Site Intelligence v${RELEASE} is already applied."
else
    git commit -m "Site Intelligence v${RELEASE} — Homepage Live Intelligence Snapshot"
fi

if git rev-parse "v${RELEASE}" >/dev/null 2>&1; then
    [[ "$(git rev-list -n 1 "v${RELEASE}")" == "$(git rev-parse HEAD)" ]] || fail "Tag v${RELEASE} already points to another commit."
else
    git tag -a "v${RELEASE}" -m "Site Intelligence v${RELEASE} — Homepage Live Intelligence Snapshot"
fi

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || fail "The Git checkout is in detached HEAD state."
git push origin "$BRANCH"
git push origin "v${RELEASE}"

printf '\nSUCCESS: Site Intelligence v%s was committed, tagged, and pushed to GitHub.\n' "$RELEASE"
