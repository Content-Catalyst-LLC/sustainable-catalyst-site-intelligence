#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.39.0"; RELEASE_ID="site-intelligence-v${RELEASE}"; RELEASE_TAG="v${RELEASE}"
REPO_SLUG="${SC_SI_GITHUB_REPOSITORY:-Content-Catalyst-LLC/sustainable-catalyst-site-intelligence}"
RENDER_URL="${SC_SI_RENDER_URL:-https://sustainable-catalyst-site-intelligence.onrender.com}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SC_SI_DEPLOY_ROOT:-$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy}"
CLONE_ROOT="$DEPLOY_ROOT/repository"; RECEIPT="$DEPLOY_ROOT/site-intelligence-v${RELEASE}-deployment-receipt.json"
ROLLBACK_TAG="site-intelligence-pre-v${RELEASE}"; BRANCH="main"; COMMIT=""; PREVIOUS_COMMIT=""; TRIGGERED="not-triggered"
write_receipt(){
  local state="${1:-preparing}" message="${2:-}"
  mkdir -p "$DEPLOY_ROOT"
  python3 - "$RECEIPT" "$RELEASE" "$RELEASE_ID" "$REPO_SLUG" "$BRANCH" "$COMMIT" "$PREVIOUS_COMMIT" "$ROLLBACK_TAG" "$TRIGGERED" "$state" "$message" <<'PY'
from datetime import datetime,timezone
from pathlib import Path
import json,sys
(path,version,release_id,repo,branch,commit,previous,rollback,trigger,state,message)=sys.argv[1:]
payload={"schema":"sc-site-intelligence-deployment-receipt/1.1","version":version,"release_id":release_id,"repository":repo,"branch":branch,"commit":commit or None,"previous_commit":previous or None,"rollback_tag":rollback,"deployment_trigger":trigger,"state":state,"message":message or None,"verification_policy":"first-party-release-identity-runtime-and-live-underwater-control-plane; upstream-health-non-blocking","updated_at":datetime.now(timezone.utc).isoformat()}
Path(path).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
}
fail(){ write_receipt "failed" "${1:-unknown failure}"; printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for c in git curl python3 rsync; do command -v "$c" >/dev/null 2>&1 || fail "$c is required."; done

printf '\n==> Validating v%s source before promotion\n' "$RELEASE"
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then PYTHON="$SOURCE_ROOT/.venv/bin/python" SC_SI_SKIP_TESTS=0 SC_SI_RUN_BROWSER=0 bash "$SOURCE_ROOT/verify_site_intelligence_v4_37_0_macos.sh"; else bash "$SOURCE_ROOT/verify_site_intelligence_v4_37_0_macos.sh"; fi

printf '\n==> Preparing clean, resume-safe GitHub deployment clone\n'
rm -rf "$CLONE_ROOT"; mkdir -p "$DEPLOY_ROOT"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then gh repo clone "$REPO_SLUG" "$CLONE_ROOT" -- --quiet; else git clone --quiet "git@github.com:${REPO_SLUG}.git" "$CLONE_ROOT" || fail 'GitHub clone failed.'; fi
git -C "$CLONE_ROOT" remote set-head origin -a >/dev/null 2>&1 || true
BRANCH="$(git -C "$CLONE_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"; [[ -n "$BRANCH" ]] || BRANCH=main
git -C "$CLONE_ROOT" checkout "$BRANCH" >/dev/null 2>&1; git -C "$CLONE_ROOT" pull --ff-only origin "$BRANCH"
REMOTE_BASE="$(git -C "$CLONE_ROOT" rev-parse "origin/$BRANCH")"
if git -C "$CLONE_ROOT" rev-parse "refs/tags/$ROLLBACK_TAG" >/dev/null 2>&1; then PREVIOUS_COMMIT="$(git -C "$CLONE_ROOT" rev-list -n 1 "$ROLLBACK_TAG")"; else PREVIOUS_COMMIT="$REMOTE_BASE"; git -C "$CLONE_ROOT" tag -a "$ROLLBACK_TAG" "$PREVIOUS_COMMIT" -m "Rollback point before Site Intelligence v${RELEASE}"; fi
write_receipt synchronizing 'Release source validated; preparing Git tree.'
rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude '.pytest_cache/' --exclude '__pycache__/' --exclude '*.pyc' --exclude '.runtime/' "$SOURCE_ROOT/" "$CLONE_ROOT/"

printf '\n==> Revalidating exact Git tree before push\n'
PYTHON_BIN="${PYTHON:-python3}"; [[ -x "$SOURCE_ROOT/.venv/bin/python" ]] && PYTHON_BIN="$SOURCE_ROOT/.venv/bin/python"
PYTHON="$PYTHON_BIN" SC_SI_SKIP_TESTS=0 SC_SI_RUN_BROWSER=0 bash "$CLONE_ROOT/verify_site_intelligence_v4_37_0_macos.sh"
cd "$CLONE_ROOT"
find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — Live Underwater Media Discovery, Imagery & Video Retrieval"
fi
COMMIT="$(git rev-parse HEAD)"; CURRENT_VERSION="$(python3 -c 'import re,pathlib;print(re.search(r"APP_VERSION\s*=\s*\"([^\"]+)",pathlib.Path("backend/app/version.py").read_text()).group(1))')"
[[ "$CURRENT_VERSION" == "$RELEASE" ]] || fail 'Deployment tree version mismatch.'
if git rev-parse "refs/tags/$RELEASE_TAG" >/dev/null 2>&1; then [[ "$(git rev-list -n 1 "$RELEASE_TAG")" == "$COMMIT" ]] || fail "Tag $RELEASE_TAG already points to another commit."; else git tag -a "$RELEASE_TAG" -m "Site Intelligence v${RELEASE} — Live Underwater Media Discovery"; fi
git fetch origin "$BRANCH" --quiet; REMOTE_NOW="$(git rev-parse "origin/$BRANCH")"
if [[ "$REMOTE_NOW" != "$REMOTE_BASE" && "$REMOTE_NOW" != "$COMMIT" ]]; then fail 'Remote branch advanced during promotion; rerun from the new head.'; fi
printf '\n==> Publishing GitHub release refs\n'
if [[ "$REMOTE_NOW" != "$COMMIT" ]]; then git push --atomic origin "$BRANCH" "$RELEASE_TAG" "$ROLLBACK_TAG"; else echo 'Release commit already on GitHub; resuming Render verification.'; git push origin "$RELEASE_TAG" "$ROLLBACK_TAG" >/dev/null 2>&1 || true; fi
write_receipt github-published 'GitHub refs synchronized; waiting for Render.'
TRIGGERED=auto-deploy
if [[ -n "${SC_SI_RENDER_DEPLOY_HOOK:-}" ]]; then sep='?'; [[ "$SC_SI_RENDER_DEPLOY_HOOK" == *'?'* ]] && sep='&'; curl -fsS -X POST "${SC_SI_RENDER_DEPLOY_HOOK}${sep}ref=${COMMIT}" >/dev/null; TRIGGERED=deploy-hook; fi
write_receipt render-pending 'Render deployment triggered or auto-deploy awaited.'

printf '\n==> Verifying Render v%s identity and underwater control plane\n' "$RELEASE"
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-24}"; INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-10}"
for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  gate="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/release-gate?plugin_version=${RELEASE}&expected_commit=${COMMIT}&expected_release_id=${RELEASE_ID}&cache_bust=${attempt}" 2>/dev/null || true)"
  read -r V C RID G < <(python3 -c 'import json,sys; d=json.load(sys.stdin); dep=d.get("deployment",{}); print(d.get("backend_version",d.get("version","?")),dep.get("git_commit","?"),d.get("release_id","?"),"ready" if d.get("install_allowed") else d.get("gate_state","blocked"))' <<<"$gate" 2>/dev/null || printf '? ? ? blocked\n')
  printf 'Render check %d/%d: version=%s gate=%s commit=%s\n' "$attempt" "$ATTEMPTS" "$V" "$G" "${C:0:12}"
  if [[ "$V" == "$RELEASE" && "$RID" == "$RELEASE_ID" && "$G" == ready && ( "$C" == "$COMMIT" || "$COMMIT" == "$C"* || "$C" == "$COMMIT"* ) ]]; then
    health="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/health?verify=$attempt" || true)"
    dep="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/deployment-verification?verify=$attempt" || true)"
    uw="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/underwater-media/readiness?verify=$attempt" || true)"
    providers="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/underwater-media/providers?verify=$attempt" || true)"
    ocean="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/ocean-observation/readiness?verify=$attempt" || true)"
    science="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/scientific-earth-systems/discovery?verify=$attempt" || true)"
    app="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/?release=${RELEASE}&verify=$attempt" || true)"
    seafloor="$(curl -fsS -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/seafloor-bathymetry-v4700.js?verify=$attempt" || true)"
    health_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")==sys.argv[1] else "false")' "$RELEASE" <<<"$health" 2>/dev/null || echo false)"
    dep_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("checks",{}); print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("contract")=="deployment-verification-live-underwater-media-v4370" and c.get("live_underwater_media_ready") and c.get("onc_underwater_credential_non_blocking") and len(d.get("required_routes",[]))==21 else "false")' "$RELEASE" <<<"$dep" 2>/dev/null || echo false)"
    uw_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("checks",{}); print("true" if d.get("ok") and d.get("version")==sys.argv[1] and c.get("three_provider_lanes_registered") and c.get("fathomnet_public_lane_ready") and c.get("noaa_public_lane_ready") and c.get("onc_missing_credential_non_blocking") and d.get("network_calls_performed") is False else "false")' "$RELEASE" <<<"$uw" 2>/dev/null || echo false)"
    providers_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); ids={x.get("id") for x in d.get("providers",[])}; print("true" if d.get("version")==sys.argv[1] and d.get("provider_count")==3 and d.get("default_provider")=="fathomnet" and ids=={"fathomnet","noaa-ocean-exploration","onc-oceans-3"} else "false")' "$RELEASE" <<<"$providers" 2>/dev/null || echo false)"
    ocean_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("system_count")==11 and d.get("systems",{}).get("underwater",{}).get("ok") is True and d.get("inherited_route_count")==35 else "false")' "$RELEASE" <<<"$ocean" 2>/dev/null || echo false)"
    science_ok="$(python3 -c 'import json,sys; d=json.load(sys.stdin); domains={x.get("id") for x in d.get("domains",[])}; print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("release_lineage")=="v4.39.0" and d.get("local_workspace_count")==8 and domains=={"earth","ocean","space"} else "false")' "$RELEASE" <<<"$science" 2>/dev/null || echo false)"
    app_ok=false; [[ "$app" == *'/app/assets/app.js?v=4.39.0'* && "$app" == *'data-ocean-entry="hub"'* && "$app" == *'data-space-entry="hub"'* && "$seafloor" == *'underwater-observation-v4800.js?v=4.39.0'* ]] && app_ok=true
    printf 'Release verification: health=%s deployment=%s underwater=%s providers=%s ocean=%s science=%s app=%s\n' "$health_ok" "$dep_ok" "$uw_ok" "$providers_ok" "$ocean_ok" "$science_ok" "$app_ok"
    if [[ "$health_ok" == true && "$dep_ok" == true && "$uw_ok" == true && "$providers_ok" == true && "$ocean_ok" == true && "$science_ok" == true && "$app_ok" == true ]]; then
      write_receipt verified 'v4.39.0 release identity, live underwater media control plane, Ocean/Space discovery and application assets synchronized.'
      printf '\nSUCCESS: Site Intelligence v%s is live with Live Underwater Media Discovery at commit %s.\nDeployment receipt: %s\nRollback tag: %s (%s)\n' "$RELEASE" "${COMMIT:0:12}" "$RECEIPT" "$ROLLBACK_TAG" "${PREVIOUS_COMMIT:0:12}"
      exit 0
    fi
  fi
  sleep "$INTERVAL"
done
fail "Render did not verify v${RELEASE} at commit ${COMMIT:0:12} within the promotion window."
