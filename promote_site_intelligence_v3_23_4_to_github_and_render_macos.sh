#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.5.0"
RELEASE_ID="site-intelligence-v${RELEASE}"
REPO_SLUG="${SC_SI_GITHUB_REPOSITORY:-Content-Catalyst-LLC/sustainable-catalyst-site-intelligence}"
RENDER_URL="${SC_SI_RENDER_URL:-https://sustainable-catalyst-site-intelligence.onrender.com}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ROOT="${SC_SI_DEPLOY_ROOT:-$HOME/Downloads/sustainable-catalyst-site-intelligence-v${RELEASE}-github-deploy}"
CLONE_ROOT="$DEPLOY_ROOT/repository"
DEPLOYMENT_RECEIPT="$DEPLOY_ROOT/site-intelligence-v${RELEASE}-deployment-receipt.json"
COMMIT=""; PREVIOUS_COMMIT=""; ROLLBACK_TAG="site-intelligence-pre-v${RELEASE}"; BRANCH="main"; TRIGGERED="not-triggered"
write_receipt(){
  local state="${1:-preparing}" message="${2:-}"
  mkdir -p "$DEPLOY_ROOT"
  python3 - "$DEPLOYMENT_RECEIPT" "$RELEASE" "$RELEASE_ID" "$REPO_SLUG" "$BRANCH" "$COMMIT" "$PREVIOUS_COMMIT" "$ROLLBACK_TAG" "$TRIGGERED" "$state" "$message" <<'PYRECEIPT'
from datetime import datetime,timezone
from pathlib import Path
import json,sys
(path,version,release_id,repo,branch,commit,previous,rollback,trigger,state,message)=sys.argv[1:]
payload={"schema":"sc-site-intelligence-deployment-receipt/1.0","version":version,"release_id":release_id,"repository":repo,"branch":branch,"commit":commit or None,"previous_commit":previous or None,"rollback_tag":rollback,"deployment_trigger":trigger,"state":state,"message":message or None,"updated_at":datetime.now(timezone.utc).isoformat()}
Path(path).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PYRECEIPT
}
fail(){ write_receipt "failed" "${1:-unknown failure}"; printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for command in git curl python3 rsync; do command -v "$command" >/dev/null 2>&1 || fail "$command is required."; done
printf '\n==> Validating release source before promotion\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$SOURCE_ROOT/verify_site_intelligence_v3_23_4_macos.sh"; else bash "$SOURCE_ROOT/verify_site_intelligence_v3_23_4_macos.sh"; fi
printf '\n==> Preparing a clean, resume-safe GitHub deployment clone\n'
rm -rf "$CLONE_ROOT"; mkdir -p "$DEPLOY_ROOT"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then gh repo clone "$REPO_SLUG" "$CLONE_ROOT" -- --quiet; else git clone --quiet "git@github.com:${REPO_SLUG}.git" "$CLONE_ROOT" || fail "GitHub clone failed."; fi
git -C "$CLONE_ROOT" remote set-head origin -a >/dev/null 2>&1 || true
BRANCH="$(git -C "$CLONE_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"; [[ -n "$BRANCH" ]] || BRANCH="main"
git -C "$CLONE_ROOT" checkout "$BRANCH" >/dev/null 2>&1; git -C "$CLONE_ROOT" pull --ff-only origin "$BRANCH"
REMOTE_BASE="$(git -C "$CLONE_ROOT" rev-parse "origin/$BRANCH")"
if git -C "$CLONE_ROOT" rev-parse "refs/tags/$ROLLBACK_TAG" >/dev/null 2>&1; then PREVIOUS_COMMIT="$(git -C "$CLONE_ROOT" rev-list -n 1 "$ROLLBACK_TAG")"; else PREVIOUS_COMMIT="$REMOTE_BASE"; git -C "$CLONE_ROOT" tag -a "$ROLLBACK_TAG" "$PREVIOUS_COMMIT" -m "Rollback point before Site Intelligence v${RELEASE}"; fi
write_receipt "synchronizing" "Release source validated; preparing Git tree."
printf '\n==> Synchronizing v%s into %s/%s\n' "$RELEASE" "$REPO_SLUG" "$BRANCH"
rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude '.pytest_cache/' --exclude '__pycache__/' --exclude '*.pyc' --exclude '.runtime/' "$SOURCE_ROOT/" "$CLONE_ROOT/"
printf '\n==> Revalidating the exact Git tree that will be pushed\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$CLONE_ROOT/verify_site_intelligence_v3_23_4_macos.sh"; else bash "$CLONE_ROOT/verify_site_intelligence_v3_23_4_macos.sh"; fi
cd "$CLONE_ROOT"
find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — analytical workspace completion"
fi
COMMIT="$(git rev-parse HEAD)"
CURRENT_VERSION="$(python3 -c 'import re,pathlib;print(re.search(r"APP_VERSION\s*=\s*\"([^\"]+)",pathlib.Path("backend/app/version.py").read_text()).group(1))')"
[[ "$CURRENT_VERSION" == "$RELEASE" ]] || fail "Deployment tree version mismatch."
if git rev-parse "refs/tags/v${RELEASE}" >/dev/null 2>&1; then [[ "$(git rev-list -n 1 "v${RELEASE}")" == "$COMMIT" ]] || fail "Tag v${RELEASE} points to another commit."; else git tag -a "v${RELEASE}" -m "Site Intelligence v${RELEASE}"; fi
git fetch origin "$BRANCH" --quiet
REMOTE_NOW="$(git rev-parse "origin/$BRANCH")"
if [[ "$REMOTE_NOW" != "$REMOTE_BASE" && "$REMOTE_NOW" != "$COMMIT" ]]; then fail "The remote branch advanced during promotion. Rerun from the new head."; fi
printf '\n==> Publishing release refs atomically or resuming an existing push\n'
if [[ "$REMOTE_NOW" != "$COMMIT" ]]; then git push --atomic origin "$BRANCH" "v${RELEASE}" "$ROLLBACK_TAG"; else printf 'Release commit is already on GitHub; resuming Render verification.\n'; git push origin "v${RELEASE}" "$ROLLBACK_TAG" >/dev/null 2>&1 || true; fi
write_receipt "github-published" "GitHub refs are synchronized; waiting for Render."
TRIGGERED="auto-deploy"
if [[ -n "${SC_SI_RENDER_DEPLOY_HOOK:-}" ]]; then sep='?'; [[ "$SC_SI_RENDER_DEPLOY_HOOK" == *'?'* ]] && sep='&'; curl -fsS -X POST "${SC_SI_RENDER_DEPLOY_HOOK}${sep}ref=${COMMIT}" >/dev/null; TRIGGERED="deploy-hook"; elif command -v render >/dev/null 2>&1 && render whoami >/dev/null 2>&1; then render deploys create "${SC_SI_RENDER_SERVICE_ID:-sustainable-catalyst-site-intelligence}" --commit "$COMMIT" --clear-cache --wait; TRIGGERED="render-cli"; fi
write_receipt "render-pending" "Render deployment triggered or auto-deploy awaited."
printf '\n==> Verifying the live Render deployment receipt and release gate\n'
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-80}"; INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-15}"
OBSERVED_VERSION=unavailable; OBSERVED_COMMIT=unavailable; OBSERVED_GATE=unavailable; OBSERVED_RELEASE_ID=unavailable
for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  endpoint="${RENDER_URL%/}/public/release-gate?plugin_version=${RELEASE}&expected_commit=${COMMIT}&expected_release_id=${RELEASE_ID}&cache_bust=${attempt}"
  payload="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Pragma: no-cache' "$endpoint" 2>/dev/null || true)"
  if [[ -n "$payload" ]]; then
    read -r OBSERVED_VERSION OBSERVED_COMMIT OBSERVED_RELEASE_ID OBSERVED_GATE < <(python3 -c 'import json,sys;d=json.load(sys.stdin);dep=d.get("deployment",{});print(d.get("backend_version",d.get("version","unavailable")),dep.get("git_commit","unavailable"),d.get("release_id","unavailable"),"ready" if d.get("install_allowed") else d.get("gate_state","blocked"))' <<<"$payload" 2>/dev/null || printf 'unavailable unavailable unavailable unavailable\n')
    if [[ "$OBSERVED_VERSION" == "$RELEASE" && "$OBSERVED_RELEASE_ID" == "$RELEASE_ID" && "$OBSERVED_GATE" == "ready" && ( "$OBSERVED_COMMIT" == "$COMMIT" || "$COMMIT" == "$OBSERVED_COMMIT"* || "$OBSERVED_COMMIT" == "$COMMIT"* ) ]]; then
      app_html="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/?release=${RELEASE}&verify=${attempt}" 2>/dev/null || true)"
      engine_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/vector-cartography-v3230.js?verify=${attempt}" 2>/dev/null || true)"
      world_geojson="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/world-cartography-v3230.geojson?verify=${attempt}" 2>/dev/null || true)"
      workspace_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/cartographic-workspace-v3230.js?verify=${attempt}" 2>/dev/null || true)"
      truth_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/production-truth-v3231.js?verify=${attempt}" 2>/dev/null || true)"
      interaction_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/cartographic-interaction-v3232.js?verify=${attempt}" 2>/dev/null || true)"
      interaction_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/maps/interaction?verify=${attempt}" 2>/dev/null || true)"
      data_truth_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/data-truth-v32371.js?verify=${attempt}" 2>/dev/null || true)"
      data_truth_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth?verify=${attempt}" 2>/dev/null || true)"
      analytical_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/analytical-workspaces-v3234.js?verify=${attempt}" 2>/dev/null || true)"
      analytical_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workflows/analytical?verify=${attempt}" 2>/dev/null || true)"
      truth_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workspaces/production-truth?verify=${attempt}" 2>/dev/null || true)"
      runtime_health="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/runtime-health?verify=${attempt}" 2>/dev/null || true)"
      app_ready=false; engine_ready=false; world_ready=false; workspace_ready=false; interaction_ready=false; data_truth_ready=false; analytical_ready=false; truth_ready=false; health_ready=false
      [[ "$app_html" == *'data-scsi-release="4.5.0"'* && "$app_html" == *'vector-cartography-v3230.js'* && "$app_html" == *'cartographic-workspace-v3230.js'* && "$app_html" == *'cartographic-interaction-v3232.js'* ]] && app_ready=true
      [[ "$engine_js" == *'__scsiSelfHosted: true'* && "$engine_js" == *'world-cartography-v3230.geojson'* ]] && engine_ready=true
      [[ "$workspace_js" == *'SCSICartographicWorkspaceV3230'* && "$workspace_js" == *'evaluateVisibleMaps'* && "$workspace_js" == *'overviewEvidenceRail'* ]] && workspace_ready=true
      interaction_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.5.0" and all(d.get("layer_controls",{}).values()) else "false")' <<<"$interaction_contract" 2>/dev/null || printf false)"
      [[ "$interaction_js" == *'SCSICartographicInteractionV3232'* && "$interaction_js" == *'mapImageryOpacity'* && "$interaction_js" == *'mapClusterEvents'* ]] || interaction_ready=false
      data_truth_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); p=d.get("classification_policy",{}); print("true" if d.get("ok") and d.get("version")=="4.5.0" and d.get("source_count")==8 and p.get("cached_is_live") is False and p.get("demonstration_is_live") is False else "false")' <<<"$data_truth_contract" 2>/dev/null || printf false)"
      [[ "$data_truth_js" == *'SCSIDataTruthV32371'* && "$data_truth_js" == *'stale_marker_required'* && "$data_truth_js" == *'dataTruthPanel'* ]] || data_truth_ready=false
      analytical_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.5.0" and d.get("workflow_count")==5 and d.get("summary",{}).get("unavailable")==0 else "false")' <<<"$analytical_contract" 2>/dev/null || printf false)"
      [[ "$analytical_js" == *'SCSIAnalyticalWorkspacesV3234'* && "$analytical_js" == *'analyticalWorkflowPanel'* && "$analytical_js" == *'insideApp'* ]] || analytical_ready=false
      truth_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.5.0" and d.get("route_count")==35 and d.get("summary",{}).get("unavailable")==0 else "false")' <<<"$truth_contract" 2>/dev/null || printf false)"
      [[ "$truth_js" == *'SCSIProductionTruthV3231'* && "$truth_js" == *'history.pushState'* && "$truth_js" == *'scsi:workspace-state'* ]] || truth_ready=false
      world_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("type")=="FeatureCollection" and len(d.get("features",[]))>=170 else "false")' <<<"$world_geojson" 2>/dev/null || printf false)"
      health_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("status")=="healthy" and d.get("version")=="4.5.0" else "false")' <<<"$runtime_health" 2>/dev/null || printf false)"
      if [[ "$app_ready" == true && "$engine_ready" == true && "$world_ready" == true && "$workspace_ready" == true && "$interaction_ready" == true && "$data_truth_ready" == true && "$analytical_ready" == true && "$truth_ready" == true && "$health_ready" == true ]]; then
        write_receipt "verified" "GitHub, Render, the live app shell, self-hosted map engine, cartographic workspace, interaction controls, data-truth directory, five-workflow analytical directory, production-truth directory, runtime health, and WordPress installation gate are synchronized."
        printf 'Render release gate and live map runtime are ready for v%s at commit %s.
' "$OBSERVED_VERSION" "${OBSERVED_COMMIT:0:12}"
        printf '
SUCCESS: Site Intelligence v4.5.0 is live with analytical workspace completion.
Deployment receipt: %s
Rollback tag: %s (%s)
' "$DEPLOYMENT_RECEIPT" "$ROLLBACK_TAG" "${PREVIOUS_COMMIT:0:12}"
        exit 0
      fi
    fi
  fi
  sleep "$INTERVAL"
done
fail "GitHub is current, but Render did not verify v${RELEASE}/${RELEASE_ID} at commit ${COMMIT}. Rerun this installer to resume verification without creating a new rollback point."
