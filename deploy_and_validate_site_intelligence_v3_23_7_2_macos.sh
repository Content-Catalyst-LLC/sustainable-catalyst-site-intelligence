#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.12.0"
RELEASE_ID="site-intelligence-v${RELEASE}"
BUNDLE="${1:-}"
fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
if [[ -z "$BUNDLE" ]]; then
  BUNDLE="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.12.0-release-bundle*.zip' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)"
fi
[[ -n "$BUNDLE" && -f "$BUNDLE" ]] || fail "The Site Intelligence v${RELEASE} release bundle was not found in Downloads."
for command_name in unzip shasum python3 git curl rsync; do command -v "$command_name" >/dev/null 2>&1 || fail "$command_name is required."; done
TARGET="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-deployment"
rm -rf "$TARGET"; mkdir -p "$TARGET"
printf '\n==> Extracting Site Intelligence v%s\n' "$RELEASE"
unzip -q "$BUNDLE" -d "$TARGET"
if [[ -f "$TARGET/SHA256SUMS.txt" ]]; then BUNDLE_ROOT="$TARGET"; else
  CHECKSUM_FILE=""; CHECKSUM_COUNT=0
  while IFS= read -r -d '' candidate; do CHECKSUM_FILE="$candidate"; CHECKSUM_COUNT=$((CHECKSUM_COUNT+1)); done < <(find "$TARGET" -mindepth 2 -maxdepth 2 -type f -name SHA256SUMS.txt -print0)
  [[ "$CHECKSUM_COUNT" -eq 1 ]] || fail "SHA256SUMS.txt was not found at a unique bundle root."
  BUNDLE_ROOT="$(dirname "$CHECKSUM_FILE")"
fi
cd "$BUNDLE_ROOT"
printf '\n==> Verifying release-bundle checksums\n'
shasum -a 256 -c SHA256SUMS.txt
REPOSITORY_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"
WORDPRESS_ZIP="$BUNDLE_ROOT/sustainable-catalyst-site-intelligence-v${RELEASE}-wordpress-plugin.zip"
[[ -f "$REPOSITORY_ZIP" && -f "$WORDPRESS_ZIP" ]] || fail "A release package is missing."
if [[ "${SC_VERIFY_BUNDLE_ONLY:-0}" == "1" ]]; then printf '\nSUCCESS: Site Intelligence v%s bundle structure and checksums verified.\n' "$RELEASE"; exit 0; fi
unzip -q "$REPOSITORY_ZIP" -d "$TARGET/repository"
ROOT="$TARGET/repository/sustainable-catalyst-site-intelligence-v${RELEASE}"
[[ -d "$ROOT" ]] || fail "The extracted repository folder is missing."
printf '\n==> Creating an isolated Python validation environment\n'
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt" -r "$ROOT/backend/requirements-dev.txt"
printf '\n==> Running deterministic validation pass 1\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v3_23_7_2_macos.sh"
printf '\n==> Running deterministic validation pass 2\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v3_23_7_2_macos.sh"
printf '\n==> Promoting the backend through GitHub and Render\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/promote_site_intelligence_v3_23_7_2_to_github_and_render_macos.sh"
RECEIPT="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy/site-intelligence-v${RELEASE}-deployment-receipt.json"
cat <<DONE

SUCCESS: Site Intelligence v${RELEASE} is live with country dropdown interaction and focus safety.
Release id: ${RELEASE_ID}

Deployment receipt:
${RECEIPT}

WordPress plugin ZIP:
${WORDPRESS_ZIP}

Install the WordPress ZIP only now that the live gate has verified the exact release, Git commit, application shell, maps, analytical workflows, browser reliability, performance/offline contract, single-owner bootstrap contract, mutation-observer recovery contract, mandatory complete-shell browser gate, service-worker strategy, production truth, and runtime health.
DONE
