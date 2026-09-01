#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.39.1"; BUNDLE="${1:-}"
fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
if [[ -z "$BUNDLE" ]]; then BUNDLE="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.39.1-release-bundle*.zip' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)"; fi
[[ -n "$BUNDLE" && -f "$BUNDLE" ]] || fail "Site Intelligence v${RELEASE} release bundle not found in Downloads."
for c in unzip shasum python3 git curl rsync; do command -v "$c" >/dev/null 2>&1 || fail "$c is required."; done
TARGET="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-deployment"; rm -rf "$TARGET"; mkdir -p "$TARGET"; unzip -q "$BUNDLE" -d "$TARGET"
if [[ -f "$TARGET/SHA256SUMS.txt" ]]; then BUNDLE_ROOT="$TARGET"; else CHECK="$(find "$TARGET" -mindepth 2 -maxdepth 2 -type f -name SHA256SUMS.txt | head -1)"; [[ -n "$CHECK" ]] || fail 'SHA256SUMS.txt missing.'; BUNDLE_ROOT="$(dirname "$CHECK")"; fi
cd "$BUNDLE_ROOT"; printf '\n==> Verifying v%s release-bundle checksums\n' "$RELEASE"; shasum -a 256 -c SHA256SUMS.txt
REPO_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"; WP_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-wordpress-plugin.zip"
[[ -f "$REPO_ZIP" && -f "$WP_ZIP" ]] || fail 'Repository or WordPress package missing.'
[[ "${SC_VERIFY_BUNDLE_ONLY:-0}" == 1 ]] && { echo "SUCCESS: v${RELEASE} bundle verified."; exit 0; }
unzip -q "$REPO_ZIP" -d "$TARGET/repository"; ROOT="$TARGET/repository/sustainable-catalyst-site-intelligence-v${RELEASE}"; [[ -d "$ROOT" ]] || fail 'Extracted repository folder missing.'
python3 -m venv "$ROOT/.venv"; "$ROOT/.venv/bin/python" -m pip install --upgrade pip; "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt" -r "$ROOT/backend/requirements-dev.txt"
printf '\n==> Running deterministic v%s validation\n' "$RELEASE"; PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v4_37_0_macos.sh"
printf '\n==> Running browser certification\n'; SC_SI_SKIP_TESTS=1 SC_SI_RUN_BROWSER=1 PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v4_37_0_macos.sh"
printf '\n==> Promoting certified tree through GitHub and Render\n'; PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/promote_site_intelligence_v4_37_0_to_github_and_render_macos.sh"
printf '\nSUCCESS: Site Intelligence v%s is live.\n\nWordPress plugin ZIP:\n%s\n\nOptional ONC configuration (Site Intelligence Render service):\nSC_SI_ONC_API_TOKEN=<Oceans 3.0 token>\nSC_SI_UNDERWATER_MEDIA_TIMEOUT_SECONDS=10\n' "$RELEASE" "$WP_ZIP"
