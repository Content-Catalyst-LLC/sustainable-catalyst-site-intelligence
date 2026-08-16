#!/usr/bin/env bash
set -euo pipefail

RELEASE="4.36.1"
BUNDLE="${1:-}"

fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }

if [[ -z "$BUNDLE" ]]; then
  BUNDLE="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.36.1-release-bundle*.zip' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)"
fi
[[ -n "$BUNDLE" && -f "$BUNDLE" ]] || fail "The Site Intelligence v${RELEASE} release bundle was not found in Downloads."

for c in unzip shasum python3 git curl rsync; do
  command -v "$c" >/dev/null 2>&1 || fail "$c is required."
done

TARGET="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-deployment"
rm -rf "$TARGET"
mkdir -p "$TARGET"
unzip -q "$BUNDLE" -d "$TARGET"

if [[ -f "$TARGET/SHA256SUMS.txt" ]]; then
  BUNDLE_ROOT="$TARGET"
else
  CHECKSUM_FILE="$(find "$TARGET" -mindepth 2 -maxdepth 2 -type f -name SHA256SUMS.txt | head -1 || true)"
  [[ -n "$CHECKSUM_FILE" ]] || fail 'SHA256SUMS.txt missing from release bundle.'
  BUNDLE_ROOT="$(dirname "$CHECKSUM_FILE")"
fi

cd "$BUNDLE_ROOT"
printf '\n==> Verifying release-bundle checksums\n'
shasum -a 256 -c SHA256SUMS.txt

REPOSITORY_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"
WORDPRESS_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-wordpress-plugin.zip"
[[ -f "$REPOSITORY_ZIP" ]] || fail 'Repository ZIP missing.'
[[ -f "$WORDPRESS_ZIP" ]] || fail 'WordPress plugin ZIP missing.'

if [[ "${SC_VERIFY_BUNDLE_ONLY:-0}" == "1" ]]; then
  printf '\nSUCCESS: Site Intelligence v%s bundle structure and checksums verified.\n' "$RELEASE"
  exit 0
fi

mkdir -p "$TARGET/repository"
unzip -q "$REPOSITORY_ZIP" -d "$TARGET/repository"
ROOT="$TARGET/repository/sustainable-catalyst-site-intelligence-v${RELEASE}"
[[ -d "$ROOT" ]] || fail 'Extracted repository folder missing.'

printf '\n==> Creating isolated Python environment\n'
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt" -r "$ROOT/backend/requirements-dev.txt"

printf '\n==> Running full deterministic v%s validation\n' "$RELEASE"
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v4_36_1_macos.sh"

if [[ "${SC_SI_RUN_BROWSER:-0}" == "1" ]]; then
  printf '\n==> Running deterministic browser evidence gate\n'
  SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON="$ROOT/.venv/bin/python" \
    bash "$ROOT/verify_site_intelligence_v4_36_1_macos.sh"
fi

if [[ "${SC_SI_SKIP_PROMOTION:-0}" == "1" ]]; then
  printf '\nSUCCESS: Site Intelligence v%s validated locally; GitHub/Render promotion was skipped.\n' "$RELEASE"
  printf 'WordPress plugin ZIP: %s\n' "$WORDPRESS_ZIP"
  exit 0
fi

printf '\n==> Publishing to GitHub and verifying Render\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/promote_site_intelligence_v4_36_1_to_github_and_render_macos.sh"

printf '\nSUCCESS: Site Intelligence v%s validated, pushed to GitHub, and verified on Render.\n' "$RELEASE"
printf 'WordPress plugin ZIP:\n%s\n' "$WORDPRESS_ZIP"
