#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.34.0"; RELEASE_ID="site-intelligence-v${RELEASE}"; BUNDLE="${1:-}"
fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
if [[ -z "$BUNDLE" ]]; then BUNDLE="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.34.0-release-bundle*.zip' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)"; fi
[[ -n "$BUNDLE" && -f "$BUNDLE" ]] || fail "The Site Intelligence v${RELEASE} release bundle was not found in Downloads."
for c in unzip shasum python3 git curl rsync; do command -v "$c" >/dev/null 2>&1 || fail "$c is required."; done
TARGET="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-deployment"; rm -rf "$TARGET"; mkdir -p "$TARGET"; unzip -q "$BUNDLE" -d "$TARGET"
if [[ -f "$TARGET/SHA256SUMS.txt" ]]; then BUNDLE_ROOT="$TARGET"; else CHECKSUM_FILE="$(find "$TARGET" -mindepth 2 -maxdepth 2 -type f -name SHA256SUMS.txt | head -1)"; [[ -n "$CHECKSUM_FILE" ]] || fail 'SHA256SUMS.txt missing.'; BUNDLE_ROOT="$(dirname "$CHECKSUM_FILE")"; fi
cd "$BUNDLE_ROOT"; printf '\n==> Verifying release-bundle checksums\n'; shasum -a 256 -c SHA256SUMS.txt
REPOSITORY_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"; WORDPRESS_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-wordpress-plugin.zip"
[[ -f "$REPOSITORY_ZIP" && -f "$WORDPRESS_ZIP" ]] || fail 'A release package is missing.'
if [[ "${SC_VERIFY_BUNDLE_ONLY:-0}" == "1" ]]; then printf '\nSUCCESS: Site Intelligence v%s bundle structure and checksums verified.\n' "$RELEASE"; exit 0; fi
unzip -q "$REPOSITORY_ZIP" -d "$TARGET/repository"; ROOT="$TARGET/repository/sustainable-catalyst-site-intelligence-v${RELEASE}"; [[ -d "$ROOT" ]] || fail 'Extracted repository folder missing.'
python3 -m venv "$ROOT/.venv"; "$ROOT/.venv/bin/python" -m pip install --upgrade pip; "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt" -r "$ROOT/backend/requirements-dev.txt"
printf '\n==> Running deterministic validation pass 1\n'; PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v4_33_0_macos.sh"
printf '\n==> Running deterministic validation pass 2\n'; SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v4_33_0_macos.sh"
printf '\n==> Promoting backend through GitHub and Render\n'; PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/promote_site_intelligence_v4_33_0_to_github_and_render_macos.sh"
printf '\nSUCCESS: Site Intelligence v%s is live with Global Solid Waste, Recycling & Circular-Materials Intelligence.\nRelease id: %s\n\nWordPress plugin ZIP:\n%s\n' "$RELEASE" "$RELEASE_ID" "$WORDPRESS_ZIP"
