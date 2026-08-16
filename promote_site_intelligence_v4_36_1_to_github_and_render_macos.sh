#!/usr/bin/env bash
set -euo pipefail

RELEASE="4.36.1"
RELEASE_ID="site-intelligence-v${RELEASE}"
RELEASE_TAG="v${RELEASE}"
REPO_SLUG="${SC_SI_GITHUB_REPOSITORY:-Content-Catalyst-LLC/sustainable-catalyst-site-intelligence}"
RENDER_URL="${SC_SI_RENDER_URL:-https://sustainable-catalyst-site-intelligence.onrender.com}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SC_SI_DEPLOY_ROOT:-$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy}"
CLONE_ROOT="$DEPLOY_ROOT/repository"
RECEIPT="$DEPLOY_ROOT/site-intelligence-v${RELEASE}-deployment-receipt.json"
ROLLBACK_TAG="site-intelligence-pre-v${RELEASE}"
BRANCH="main"
COMMIT=""
PREVIOUS_COMMIT=""
TRIGGERED="auto-deploy"

fail(){ printf '\nERROR: %s\n' "$1" >&2; write_receipt "failed" "$1" || true; exit 1; }

write_receipt(){
  local state="${1:-preparing}" message="${2:-}"
  mkdir -p "$DEPLOY_ROOT"
  python3 - "$RECEIPT" "$RELEASE" "$RELEASE_ID" "$REPO_SLUG" "$BRANCH" "$COMMIT" "$PREVIOUS_COMMIT" "$ROLLBACK_TAG" "$TRIGGERED" "$state" "$message" <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import json, sys
path, version, release_id, repo, branch, commit, previous, rollback, trigger, state, message = sys.argv[1:]
payload = {
    "schema": "sc-site-intelligence-deployment-receipt/1.2",
    "version": version,
    "release_id": release_id,
    "repository": repo,
    "branch": branch,
    "commit": commit or None,
    "previous_commit": previous or None,
    "rollback_tag": rollback,
    "deployment_trigger": trigger,
    "state": state,
    "message": message or None,
    "verification_policy": "release identity + first-party runtime; external-provider health non-blocking",
    "updated_at": datetime.now(timezone.utc).isoformat(),
}
Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY
}

for c in git curl python3 rsync; do
  command -v "$c" >/dev/null 2>&1 || fail "$c is required."
done

printf '\n==> Validating v%s source before GitHub promotion\n' "$RELEASE"
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  SC_SI_SKIP_TESTS="${SC_SI_PROMOTION_SKIP_TESTS:-0}" PYTHON="$SOURCE_ROOT/.venv/bin/python" \
    bash "$SOURCE_ROOT/verify_site_intelligence_v4_36_1_macos.sh"
else
  SC_SI_SKIP_TESTS="${SC_SI_PROMOTION_SKIP_TESTS:-0}" \
    bash "$SOURCE_ROOT/verify_site_intelligence_v4_36_1_macos.sh"
fi

printf '\n==> Preparing clean GitHub deployment clone\n'
rm -rf "$CLONE_ROOT"
mkdir -p "$DEPLOY_ROOT"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh repo clone "$REPO_SLUG" "$CLONE_ROOT" -- --quiet
else
  git clone --quiet "git@github.com:${REPO_SLUG}.git" "$CLONE_ROOT" || fail "GitHub clone failed. Authenticate with gh or SSH first."
fi

git -C "$CLONE_ROOT" remote set-head origin -a >/dev/null 2>&1 || true
BRANCH="$(git -C "$CLONE_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
[[ -n "$BRANCH" ]] || BRANCH="main"
git -C "$CLONE_ROOT" checkout "$BRANCH" >/dev/null 2>&1
git -C "$CLONE_ROOT" pull --ff-only origin "$BRANCH"
REMOTE_BASE="$(git -C "$CLONE_ROOT" rev-parse "origin/$BRANCH")"
PREVIOUS_COMMIT="$REMOTE_BASE"

if git -C "$CLONE_ROOT" rev-parse "refs/tags/$ROLLBACK_TAG" >/dev/null 2>&1; then
  PREVIOUS_COMMIT="$(git -C "$CLONE_ROOT" rev-list -n 1 "$ROLLBACK_TAG")"
else
  git -C "$CLONE_ROOT" tag -a "$ROLLBACK_TAG" "$PREVIOUS_COMMIT" -m "Rollback point before Site Intelligence v${RELEASE}"
fi
write_receipt "synchronizing" "Release source validated; synchronizing exact release tree."

rsync -a --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.runtime/' \
  "$SOURCE_ROOT/" "$CLONE_ROOT/"

printf '\n==> Revalidating exact Git tree\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  SC_SI_SKIP_TESTS=1 PYTHON="$SOURCE_ROOT/.venv/bin/python" \
    bash "$CLONE_ROOT/verify_site_intelligence_v4_36_1_macos.sh"
else
  SC_SI_SKIP_TESTS=1 bash "$CLONE_ROOT/verify_site_intelligence_v4_36_1_macos.sh"
fi

cd "$CLONE_ROOT"
find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true

git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — Ocean & Space Live Evidence Rendering, Connector Binding & OpenAPI Recovery"
fi
COMMIT="$(git rev-parse HEAD)"

CURRENT_VERSION="$(python3 - <<'PY'
import re
from pathlib import Path
m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', Path('backend/app/version.py').read_text())
print(m.group(1) if m else '')
PY
)"
[[ "$CURRENT_VERSION" == "$RELEASE" ]] || fail "Deployment tree version mismatch: $CURRENT_VERSION"

if git rev-parse "refs/tags/$RELEASE_TAG" >/dev/null 2>&1; then
  [[ "$(git rev-list -n 1 "$RELEASE_TAG")" == "$COMMIT" ]] || fail "Tag $RELEASE_TAG already points to another commit."
else
  git tag -a "$RELEASE_TAG" -m "Site Intelligence v${RELEASE}"
fi

git fetch origin "$BRANCH" --quiet
REMOTE_NOW="$(git rev-parse "origin/$BRANCH")"
if [[ "$REMOTE_NOW" != "$REMOTE_BASE" && "$REMOTE_NOW" != "$COMMIT" ]]; then
  fail "The remote branch advanced during promotion. Rerun from the new head."
fi

printf '\n==> Pushing v%s to GitHub\n' "$RELEASE"
if [[ "$REMOTE_NOW" != "$COMMIT" ]]; then
  git push --atomic origin "$BRANCH" "$RELEASE_TAG" "$ROLLBACK_TAG"
else
  printf 'Release commit is already on GitHub; resuming deployment verification.\n'
  git push origin "$RELEASE_TAG" "$ROLLBACK_TAG" >/dev/null 2>&1 || true
fi
write_receipt "github-published" "GitHub branch and release tags are synchronized."

if [[ -n "${SC_SI_RENDER_DEPLOY_HOOK:-}" ]]; then
  sep='?'; [[ "$SC_SI_RENDER_DEPLOY_HOOK" == *'?'* ]] && sep='&'
  curl -fsS -X POST "${SC_SI_RENDER_DEPLOY_HOOK}${sep}ref=${COMMIT}" >/dev/null
  TRIGGERED="deploy-hook"
elif command -v render >/dev/null 2>&1 && render whoami >/dev/null 2>&1; then
  render deploys create "${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence}" --commit "$COMMIT" --clear-cache --wait
  TRIGGERED="render-cli"
else
  TRIGGERED="auto-deploy"
fi
write_receipt "render-pending" "Render deployment triggered or auto-deploy awaited."

printf '\n==> Waiting for Render v%s\n' "$RELEASE"
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-30}"
INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-10}"
verified=0
for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  health="$(curl -sS --connect-timeout 4 --max-time 12 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/health?verify=${attempt}" 2>/dev/null || true)"
  observed="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("version", ""))' <<<"$health" 2>/dev/null || true)"
  printf 'Render check %d/%d: version=%s\n' "$attempt" "$ATTEMPTS" "${observed:-unavailable}"
  if [[ "$observed" == "$RELEASE" ]]; then
    openapi_code="$(curl -sS -o "$DEPLOY_ROOT/openapi.json" -w '%{http_code}' --connect-timeout 4 --max-time 20 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/openapi.json?verify=${attempt}" 2>/dev/null || true)"
    ocean="$(curl -sS --connect-timeout 4 --max-time 12 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/ocean-observation/readiness?verify=${attempt}" 2>/dev/null || true)"
    science="$(curl -sS --connect-timeout 4 --max-time 12 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/scientific-earth-systems/discovery?verify=${attempt}" 2>/dev/null || true)"
    ready="$(python3 - "$RELEASE" "$openapi_code" "$DEPLOY_ROOT/openapi.json" <<'PY'
import json, sys
version, code, path = sys.argv[1:]
try:
    schema = json.load(open(path))
except Exception:
    schema = {}
required = {
    '/public/authoritative-connectors/noaa-erddap/search',
    '/public/authoritative-connectors/noaa-coops/data',
    '/public/authoritative-connectors/obis/occurrences',
    '/public/authoritative-connectors/nasa-exoplanets',
    '/public/authoritative-connectors/nasa-cmr/collections',
}
ok = code == '200' and schema.get('info', {}).get('version') == version and required.issubset(schema.get('paths', {}))
print('true' if ok else 'false')
PY
)"
    ocean_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("system_count")==11 else "false")' "$RELEASE" <<<"$ocean" 2>/dev/null || printf false)"
    science_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); acts={x.get("action") for x in d.get("workspaces",[])}; needed={"ocean","orbital-earth","planetary","astronomy","solar-system","exoplanets","seti"}; print("true" if d.get("ok") and d.get("version")==sys.argv[1] and needed.issubset(acts) else "false")' "$RELEASE" <<<"$science" 2>/dev/null || printf false)"
    printf 'First-party gates: openapi=%s ocean=%s science=%s\n' "$ready" "$ocean_ready" "$science_ready"
    if [[ "$ready" == true && "$ocean_ready" == true && "$science_ready" == true ]]; then
      verified=1
      break
    fi
  fi
  sleep "$INTERVAL"
done
[[ "$verified" == 1 ]] || fail "Render did not verify v${RELEASE} first-party runtime within the configured window."

if [[ "${SC_SI_RUN_LIVE_PROVIDER_PROBES:-0}" == "1" ]]; then
  printf '\n==> Optional live-provider probes (non-blocking)\n'
  probe(){
    local label="$1"; shift
    local code
    code="$(curl -sS -o /tmp/sc-si-provider-probe.json -w '%{http_code}' --connect-timeout 5 --max-time 25 "$@" 2>/dev/null || true)"
    printf '%-28s HTTP %s\n' "$label" "${code:-unavailable}"
  }
  probe "NOAA ERDDAP" --get "${RENDER_URL%/}/public/authoritative-connectors/noaa-erddap/search" --data-urlencode 'query=sea surface temperature' --data-urlencode 'limit=5'
  probe "NOAA CO-OPS" --get "${RENDER_URL%/}/public/authoritative-connectors/noaa-coops/data" --data-urlencode 'station=9414290'
  probe "OBIS" --get "${RENDER_URL%/}/public/authoritative-connectors/obis/occurrences" --data-urlencode 'scientific_name=Delphinus delphis' --data-urlencode 'size=5'
  probe "NASA Exoplanets" --get "${RENDER_URL%/}/public/authoritative-connectors/nasa-exoplanets" --data-urlencode 'target=TRAPPIST-1 e' --data-urlencode 'limit=5'
  probe "NASA CMR" --get "${RENDER_URL%/}/public/authoritative-connectors/nasa-cmr/collections" --data-urlencode 'query=Mars' --data-urlencode 'limit=5'
  rm -f /tmp/sc-si-provider-probe.json
  printf 'Provider probes are operational evidence only and do not block release promotion.\n'
fi

write_receipt "verified" "GitHub and Render verified v4.36.1 with OpenAPI recovery, 11-system Ocean readiness, and Earth/Ocean/Space discovery."
printf '\nSUCCESS: Site Intelligence v%s is live at commit %s.\n' "$RELEASE" "${COMMIT:0:12}"
printf 'Deployment receipt: %s\n' "$RECEIPT"
printf 'Rollback tag: %s (%s)\n' "$ROLLBACK_TAG" "${PREVIOUS_COMMIT:0:12}"
