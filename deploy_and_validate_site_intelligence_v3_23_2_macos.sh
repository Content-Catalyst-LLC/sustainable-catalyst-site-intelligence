#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.0.0"
RELEASE_ID="site-intelligence-v${RELEASE}"
BUNDLE="${1:-}"
fail(){ printf '\nERROR: %s\n' "$1" >&2; exit 1; }
if [[ -z "$BUNDLE" ]]; then
  BUNDLE="$(find "$HOME/Downloads" -maxdepth 1 -type f -name 'sustainable-catalyst-site-intelligence-v4.0.0-release-bundle*.zip' -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)"
fi
[[ -n "$BUNDLE" && -f "$BUNDLE" ]] || fail "The Site Intelligence v${RELEASE} release bundle was not found in Downloads."
for command in unzip shasum python3 git curl rsync; do command -v "$command" >/dev/null 2>&1 || fail "$command is required."; done
TARGET="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-deployment"
rm -rf "$TARGET"; mkdir -p "$TARGET"
printf '\n==> Extracting Site Intelligence v%s\n' "$RELEASE"
unzip -q "$BUNDLE" -d "$TARGET"; cd "$TARGET"
[[ -f SHA256SUMS.txt ]] || fail "SHA256SUMS.txt is missing from the release bundle."
printf '\n==> Verifying release-bundle checksums\n'; shasum -a 256 -c SHA256SUMS.txt
REPOSITORY_ZIP="$TARGET/sustainable-catalyst-site-intelligence-v${RELEASE}-repository.zip"
WORDPRESS_ZIP="$TARGET/sustainable-catalyst-site-intelligence-v${RELEASE}-wordpress-plugin.zip"
[[ -f "$REPOSITORY_ZIP" ]] || fail "The repository ZIP is missing."
[[ -f "$WORDPRESS_ZIP" ]] || fail "The WordPress ZIP is missing."
unzip -q "$REPOSITORY_ZIP" -d "$TARGET/repository"
ROOT="$TARGET/repository/sustainable-catalyst-site-intelligence-v${RELEASE}"
[[ -d "$ROOT" ]] || fail "The extracted repository folder is missing."
printf '\n==> Creating an isolated Python validation environment\n'
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt" -r "$ROOT/backend/requirements-dev.txt"
printf '\n==> Running deterministic validation pass 1\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v3_23_2_macos.sh"
printf '\n==> Running deterministic validation pass 2\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/verify_site_intelligence_v3_23_2_macos.sh"
printf '\n==> Promoting the backend through GitHub and Render\n'
PYTHON="$ROOT/.venv/bin/python" bash "$ROOT/promote_site_intelligence_v3_23_2_to_github_and_render_macos.sh"
DEPLOYMENT_RECEIPT="$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy/site-intelligence-v${RELEASE}-deployment-receipt.json"
cat <<DONE

SUCCESS: Site Intelligence v${RELEASE} is live with cartographic interaction and layer control.
Release id: ${RELEASE_ID}

Deployment receipt:
${DEPLOYMENT_RECEIPT}

WordPress plugin ZIP:
${WORDPRESS_ZIP}

Install the WordPress ZIP only now that the live gate has verified the exact release id, Git commit, app shell, map engine, interaction controls, production-truth directory, local geography, and runtime health.
DONE
