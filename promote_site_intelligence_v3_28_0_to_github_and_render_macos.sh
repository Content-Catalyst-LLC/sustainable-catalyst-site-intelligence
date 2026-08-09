#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.2.0"
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
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$SOURCE_ROOT/verify_site_intelligence_v3_28_0_macos.sh"; else bash "$SOURCE_ROOT/verify_site_intelligence_v3_28_0_macos.sh"; fi
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
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$CLONE_ROOT/verify_site_intelligence_v3_28_0_macos.sh"; else bash "$CLONE_ROOT/verify_site_intelligence_v3_28_0_macos.sh"; fi
cd "$CLONE_ROOT"
find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — monitoring digests and early-warning operations"
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
      app_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/app.js?verify=${attempt}" 2>/dev/null || true)"
      app_css="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/app.css?verify=${attempt}" 2>/dev/null || true)"
      country_catalog_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/countries?verify=${attempt}" 2>/dev/null || true)"
      engine_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/vector-cartography-v3230.js?verify=${attempt}" 2>/dev/null || true)"
      world_geojson="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/world-cartography-v3230.geojson?verify=${attempt}" 2>/dev/null || true)"
      workspace_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/cartographic-workspace-v3230.js?verify=${attempt}" 2>/dev/null || true)"
      truth_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/production-truth-v3231.js?verify=${attempt}" 2>/dev/null || true)"
      interaction_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/cartographic-interaction-v3232.js?verify=${attempt}" 2>/dev/null || true)"
      interaction_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/maps/interaction?verify=${attempt}" 2>/dev/null || true)"
      data_truth_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/data-truth-v32371.js?verify=${attempt}" 2>/dev/null || true)"
      data_truth_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth?verify=${attempt}" 2>/dev/null || true)"
      country_truth_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/country/BRA?verify=${attempt}" 2>/dev/null || true)"
      country_matrix_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/coverage-matrix?countries=KEN,GHA,USA,IND,BRA,DEU&verify=${attempt}" 2>/dev/null || true)"
      record_truth_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/record-provenance-v3238.js?verify=${attempt}" 2>/dev/null || true)"
      record_truth_indicator="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/record-truth/indicator/KEN/SP.POP.TOTL?verify=${attempt}" 2>/dev/null || true)"
      record_truth_manifest="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/record-truth/manifest?country=KEN&verify=${attempt}" 2>/dev/null || true)"
      control_plane_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/data-truth-control-plane-v3240.js?verify=${attempt}" 2>/dev/null || true)"
      control_plane_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/control-plane?verify=${attempt}" 2>/dev/null || true)"
      control_plane_schema="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/control-plane/schema-drift?verify=${attempt}" 2>/dev/null || true)"
      control_plane_outages="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/control-plane/outages?verify=${attempt}" 2>/dev/null || true)"
      control_plane_coverage="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/control-plane/coverage?countries=KEN,BRA,USA&verify=${attempt}" 2>/dev/null || true)"
      control_plane_workspaces="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/data-truth/control-plane/workspaces?country=BRA&verify=${attempt}" 2>/dev/null || true)"
      analytical_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/analytical-workspaces-v3234.js?verify=${attempt}" 2>/dev/null || true)"
      analytical_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workflows/analytical?verify=${attempt}" 2>/dev/null || true)"
      unified_state_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/cross-view-state-v3250.js?verify=${attempt}" 2>/dev/null || true)"
      unified_state_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workspaces/unified-state?verify=${attempt}" 2>/dev/null || true)"
      unified_handoff_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Content-Type: application/json' -X POST -d '{"view":"country","country":"BRA","compare":"IND","indicator":"population"}' "${RENDER_URL%/}/public/workspaces/unified-state/handoff/compare?verify=${attempt}" 2>/dev/null || true)"
      assurance_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/assurance-v3260.js?verify=${attempt}" 2>/dev/null || true)"
      assurance_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/assurance?verify=${attempt}" 2>/dev/null || true)"
      assurance_cards="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/assurance/model-cards?verify=${attempt}" 2>/dev/null || true)"
      assurance_scenario="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Content-Type: application/json' -X POST -d '{"baseline":100,"assumptions":[{"id":"demand","mode":"percent","low":-5,"base":10,"high":20}]}' "${RENDER_URL%/}/public/assurance/scenario?verify=${attempt}" 2>/dev/null || true)"
      research_integration_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/research-integration-v3270.js?verify=${attempt}" 2>/dev/null || true)"
      research_integration_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/research-integration?verify=${attempt}" 2>/dev/null || true)"
      monitoring_operations_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/monitoring-operations-v3280.js?verify=${attempt}" 2>/dev/null || true)"
      monitoring_operations_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/monitoring-operations?verify=${attempt}" 2>/dev/null || true)"
      monitoring_feed_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/monitoring-operations/feed-contract?verify=${attempt}" 2>/dev/null || true)"
      monitoring_warning_preview="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Content-Type: application/json' -X POST --data '{"model_id":"live-gate","model_output":0.8,"threshold":0.7}' "${RENDER_URL%/}/public/monitoring-operations/modeled-warning/preview?verify=${attempt}" 2>/dev/null || true)"
      research_workbench_preview="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' -H 'Content-Type: application/json' -X POST -d '{"title":"Live gate research context","question":"Verify handoff boundary","countries":["BRA"],"records":[{"id":"gate-record","title":"Gate indicator","record_type":"indicator","evidence_class":"official-statistic","country":"BRA","indicator_id":"gate-indicator","value":1,"unit":"index","source_id":"gate-source","source_url":"https://example.org/source","retrieved_at":"2026-08-06T00:00:00Z"}]}' "${RENDER_URL%/}/public/research-integration/handoff/workbench/preview?verify=${attempt}" 2>/dev/null || true)"
      browser_reliability_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/browser-reliability-v3235.js?verify=${attempt}" 2>/dev/null || true)"
      browser_reliability_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/browser-reliability?verify=${attempt}" 2>/dev/null || true)"
      performance_offline_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/performance-offline-v3236.js?verify=${attempt}" 2>/dev/null || true)"
      performance_offline_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/performance-offline?verify=${attempt}" 2>/dev/null || true)"
      startup_stability_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/startup-stability-v32364.js?verify=${attempt}" 2>/dev/null || true)"
      startup_stability_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/startup-stability?verify=${attempt}" 2>/dev/null || true)"
      bootstrap_recovery_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/bootstrap-recovery?verify=${attempt}" 2>/dev/null || true)"
      mutation_recovery_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/mutation-observer-recovery?verify=${attempt}" 2>/dev/null || true)"
      embed_isolation_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/embed-isolation?verify=${attempt}" 2>/dev/null || true)"
      bootstrap_js="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/bootstrap-v32361.js?verify=${attempt}" 2>/dev/null || true)"
      service_worker="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/service-worker.js?verify=${attempt}" 2>/dev/null || true)"
      truth_contract="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workspaces/production-truth?verify=${attempt}" 2>/dev/null || true)"
      runtime_health="$(curl -fsS --max-time 45 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/runtime-health?verify=${attempt}" 2>/dev/null || true)"
      app_ready=false; selector_ready=false; selector_interaction_ready=false; engine_ready=false; world_ready=false; workspace_ready=false; interaction_ready=false; data_truth_ready=false; country_truth_ready=false; country_matrix_ready=false; record_truth_ready=false; control_plane_ready=false; unified_state_ready=false; assurance_ready=false; research_integration_ready=false; monitoring_operations_ready=false; analytical_ready=false; browser_reliability_ready=false; performance_offline_ready=false; startup_stability_ready=false; bootstrap_recovery_ready=false; mutation_recovery_ready=false; embed_isolation_ready=false; truth_ready=false; health_ready=false
      [[ "$app_html" == *'data-scsi-release="4.2.0"'* && "$app_html" == *'vector-cartography-v3230.js'* && "$app_html" == *'cartographic-workspace-v3230.js'* && "$app_html" == *'cartographic-interaction-v3232.js'* && "$app_html" == *'data-truth-control-plane-v3240.js?v=4.2.0'* && "$app_html" == *'cross-view-state-v3250.js?v=4.2.0'* && "$app_html" == *'assurance-v3260.js?v=4.2.0'* && "$app_html" == *'research-integration-v3270.js?v=4.2.0'* ]] && app_ready=true
      selector_catalog_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("country_count",0)>=170 else "false")' <<<"$country_catalog_contract" 2>/dev/null || printf false)"
      [[ "$app_js" == *'const countryCatalogTask=hydrateCountrySelector(initialCountry)'* && "$app_js" == *'/public/data-truth/countries'* && "$app_js" == *'scsi:country-catalog-ready'* && "$selector_catalog_ready" == true ]] && selector_ready=true
      [[ "$browser_reliability_js" == *'function userControlFocused()'* && "$browser_reliability_js" == *"if(!next||next===lastRoute)return"* && "$browser_reliability_js" == *'if(userControlFocused())return'* && "$app_css" == *'#countrySelect{touch-action:auto;overscroll-behavior:auto;scroll-behavior:auto}'* ]] && selector_interaction_ready=true
      [[ "$engine_js" == *'__scsiSelfHosted: true'* && "$engine_js" == *'world-cartography-v3230.geojson'* ]] && engine_ready=true
      [[ "$workspace_js" == *'SCSICartographicWorkspaceV3230'* && "$workspace_js" == *'evaluateVisibleMaps'* && "$workspace_js" == *'overviewEvidenceRail'* ]] && workspace_ready=true
      interaction_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.2.0" and all(d.get("layer_controls",{}).values()) else "false")' <<<"$interaction_contract" 2>/dev/null || printf false)"
      [[ "$interaction_js" == *'SCSICartographicInteractionV3232'* && "$interaction_js" == *'mapImageryOpacity'* && "$interaction_js" == *'mapClusterEvents'* ]] || interaction_ready=false
      data_truth_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); p=d.get("classification_policy",{}); print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("source_count")==8 and p.get("cached_is_live") is False and p.get("demonstration_is_live") is False else "false")' <<<"$data_truth_contract" 2>/dev/null || printf false)"
      country_truth_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("country",{}).get("code")=="BRA" and d.get("source_count")==8 else "false")' <<<"$country_truth_contract" 2>/dev/null || printf false)"
      country_matrix_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("country_count")==6 and d.get("source_count")==8 else "false")' <<<"$country_matrix_contract" 2>/dev/null || printf false)"
      [[ "$data_truth_js" == *'SCSIDataTruthV32371'* && "$data_truth_js" == *'stale_marker_required'* && "$data_truth_js" == *'dataTruthPanel'* ]] || data_truth_ready=false
      record_truth_indicator_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);f=d.get("fingerprint",{}).get("value","");print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("record_id")=="indicator:KEN:SP.POP.TOTL" and d.get("truth_state")=="historical_snapshot" and len(f)==64 else "false")' <<<"$record_truth_indicator" 2>/dev/null || printf false)"
      record_truth_manifest_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("entry_count",0)>=13 and len(d.get("manifest_fingerprint", ""))==64 else "false")' <<<"$record_truth_manifest" 2>/dev/null || printf false)"
      [[ "$record_truth_js" == *'SCSIRecordProvenanceV3238'* && "$record_truth_js" == *'/public/record-truth/manifest'* && "$record_truth_indicator_ready" == true && "$record_truth_manifest_ready" == true ]] && record_truth_ready=true
      control_plane_overview_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);s=d.get("summary",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("source_count")==8 and len(d.get("control_plane_fingerprint", ""))==64 and sum(s.get(k,0) for k in ("operational","degraded","review","unavailable","unknown"))==8 else "false")' <<<"$control_plane_contract" 2>/dev/null || printf false)"
      control_plane_schema_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("source_count")==8 else "false")' <<<"$control_plane_schema" 2>/dev/null || printf false)"
      control_plane_outages_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("incident_count")==len(d.get("incidents",[])) else "false")' <<<"$control_plane_outages" 2>/dev/null || printf false)"
      control_plane_coverage_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("country_count")==3 and d.get("source_count")==8 and sum(d.get("state_counts",{}).values())==24 else "false")' <<<"$control_plane_coverage" 2>/dev/null || printf false)"
      control_plane_workspaces_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("country",{}).get("code")=="BRA" and d.get("workspace_count")==12 else "false")' <<<"$control_plane_workspaces" 2>/dev/null || printf false)"
      [[ "$control_plane_js" == *'SCSIDataTruthControlPlaneV3240'* && "$control_plane_js" == *'/public/data-truth/control-plane/export'* && "$control_plane_overview_ready" == true && "$control_plane_schema_ready" == true && "$control_plane_outages_ready" == true && "$control_plane_coverage_ready" == true && "$control_plane_workspaces_ready" == true ]] && control_plane_ready=true
      unified_state_contract_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="unified-analytical-workspace-state" and d.get("route_count")==6 and d.get("country_catalog_count",0)>=170 else "false")' <<<"$unified_state_contract" 2>/dev/null || printf false)"
      unified_handoff_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);s=d.get("state",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="cross-view-analytical-handoff" and d.get("target")=="compare" and s.get("country")=="BRA" and s.get("compare")=="IND" and "country=BRA" in d.get("path","") else "false")' <<<"$unified_handoff_contract" 2>/dev/null || printf false)"
      [[ "$unified_state_js" == *'SiteIntelligenceCrossViewState'* && "$unified_state_js" == *'scsi:cross-view-ready'* && "$unified_state_contract_ready" == true && "$unified_handoff_ready" == true ]] && unified_state_ready=true
      assurance_contract_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="comparative-scenario-model-assurance" and len(d.get("comparison_dimensions",[]))>=6 else "false")' <<<"$assurance_contract" 2>/dev/null || printf false)"
      assurance_cards_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("method_card_count",0)>=2 else "false")' <<<"$assurance_cards" 2>/dev/null || printf false)"
      assurance_scenario_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);u=d.get("uncertainty_envelope",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="scenario-assurance-review" and d.get("base_outcome")==110 and u.get("probabilistic") is False else "false")' <<<"$assurance_scenario" 2>/dev/null || printf false)"
      [[ "$assurance_js" == *'SCSIAssuranceV3260'* && "$assurance_contract_ready" == true && "$assurance_cards_ready" == true && "$assurance_scenario_ready" == true ]] && assurance_ready=true
      research_integration_contract_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="research-evidence-and-knowledge-integration" and len(d.get("targets",{}))==4 and d.get("human_confirmation_required") is True and d.get("automatic_delivery") is False else "false")' <<<"$research_integration_contract" 2>/dev/null || printf false)"
      research_workbench_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);p=d.get("packet",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and p.get("target")=="workbench" and p.get("preview_only") is True and p.get("delivery_attempted") is False and p.get("human_confirmation_required") is True else "false")' <<<"$research_workbench_preview" 2>/dev/null || printf false)"
      [[ "$research_integration_js" == *'SCSIResearchIntegrationV3270'* && "$research_integration_contract_ready" == true && "$research_workbench_ready" == true ]] && research_integration_ready=true
      monitoring_operations_contract_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="monitoring-digests-and-early-warning-operations" and len(d.get("alert_states",[]))==5 and len(d.get("watch_types",[]))==4 and d.get("human_review_required") is True and d.get("automatic_publication") is False and d.get("automatic_emergency_dispatch") is False else "false")' <<<"$monitoring_operations_contract" 2>/dev/null || printf false)"
      monitoring_feed_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("published_items_must_be_human_approved") is True and d.get("subscriber_profile_required") is False else "false")' <<<"$monitoring_feed_contract" 2>/dev/null || printf false)"
      monitoring_warning_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);w=d.get("warning",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and w.get("modeled_warning") is True and w.get("source_alert") is False and w.get("operational_emergency_alert") is False and w.get("automatic_action") is False else "false")' <<<"$monitoring_warning_preview" 2>/dev/null || printf false)"
      [[ "$monitoring_operations_js" == *'SCSIMonitoringOperationsV3280'* && "$monitoring_operations_contract_ready" == true && "$monitoring_feed_ready" == true && "$monitoring_warning_ready" == true ]] && monitoring_operations_ready=true
      analytical_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("workflow_count")==5 and d.get("summary",{}).get("unavailable")==0 else "false")' <<<"$analytical_contract" 2>/dev/null || printf false)"
      [[ "$analytical_js" == *'SCSIAnalyticalWorkspacesV3234'* && "$analytical_js" == *'analyticalWorkflowPanel'* && "$analytical_js" == *'insideApp'* ]] || analytical_ready=false
      browser_reliability_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);a=d.get("accessibility",{});r=d.get("reliability",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="browser-reliability-mobile-accessibility" and a.get("map_text_summaries") and a.get("form_control_focus_protection") and a.get("native_select_scroll_preserved") and a.get("route_focus_only_on_route_change") and r.get("repeated_workspace_state_does_not_refocus") else "false")' <<<"$browser_reliability_contract" 2>/dev/null || printf false)"
      [[ "$browser_reliability_js" == *'SCSIBrowserReliabilityV3235'* && "$browser_reliability_js" == *'scsi:viewport-recovery'* && "$browser_reliability_js" == *'Low-bandwidth mode'* ]] || browser_reliability_ready=false
      performance_offline_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="performance-and-offline-recovery" and d.get("loading",{}).get("route_request_cancellation") else "false")' <<<"$performance_offline_contract" 2>/dev/null || printf false)"
      [[ "$performance_offline_js" == *'SCSIPerformanceOfflineV3236'* && "$performance_offline_js" == *'scsi:first-useful-map'* && "$service_worker" == *'cacheFirstImmutable'* && "$service_worker" == *'X-SCSI-Data-State'* ]] || performance_offline_ready=false
      startup_stability_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);s=d.get("startup",{});w=d.get("service_worker",{});r=d.get("route_stability",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and s.get("network_data_blocks_shell") is False and s.get("initial_data_strategy")=="background-all-settled" and w.get("automatic_controllerchange_reload") is False and w.get("install_calls_skip_waiting") is False and r.get("concurrent_route_transitions") is False else "false")' <<<"$startup_stability_contract" 2>/dev/null || printf false)"
      [[ "$startup_stability_js" == *'SCSIStartupStabilityV32364'* && "$startup_stability_js" == *'HARD_FAIL_OPEN_MS=4500'* && "$service_worker" == *'event.waitUntil(installCritical())'* && "$service_worker" != *'installCritical().then(()=>self.skipWaiting())'* ]] || startup_stability_ready=false
      bootstrap_recovery_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("contract")=="single-owner-bootstrap-and-loading-recovery" and d.get("service_worker",{}).get("registration_owner_count")==1 else "false")' <<<"$bootstrap_recovery_contract" 2>/dev/null || printf false)"
      [[ "$bootstrap_js" == *'SCSIBootstrapV32361'* && "$bootstrap_js" == *'serviceWorker.register'* && "$bootstrap_js" == *'startup deadline exceeded'* ]] || bootstrap_recovery_ready=false
      mutation_recovery_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);m=d.get("mutation_observer",{});g=d.get("complete_shell_gate",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and m.get("self_observation_prevented") and g.get("required") and g.get("skip_allowed") is False else "false")' <<<"$mutation_recovery_contract" 2>/dev/null || printf false)"
      [[ "$browser_reliability_js" == *'summary.textContent!==nextText'* && "$browser_reliability_js" == *'requestAnimationFrame(flushMapSummaries)'* && "$browser_reliability_js" == *'state.observer?.disconnect()'* && "$browser_reliability_js" == *'MAX_SUMMARY_PASSES_PER_SECOND=8'* ]] || mutation_recovery_ready=false
      embed_isolation_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);a=d.get("application_embed",{});m=d.get("message_policy",{});print("true" if d.get("ok") and d.get("version")=="4.2.0" and a.get("document_auto_resize") is False and a.get("internal_scrolling") and m.get("child_height_messages_enabled") is False else "false")' <<<"$embed_isolation_contract" 2>/dev/null || printf false)"
      truth_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("version")=="4.2.0" and d.get("route_count")==35 and d.get("summary",{}).get("unavailable")==0 else "false")' <<<"$truth_contract" 2>/dev/null || printf false)"
      [[ "$truth_js" == *'SCSIProductionTruthV3231'* && "$truth_js" == *'history.pushState'* && "$truth_js" == *'scsi:workspace-state'* ]] || truth_ready=false
      world_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("type")=="FeatureCollection" and len(d.get("features",[]))>=170 else "false")' <<<"$world_geojson" 2>/dev/null || printf false)"
      health_ready="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d.get("ok") and d.get("status")=="healthy" and d.get("version")=="4.2.0" else "false")' <<<"$runtime_health" 2>/dev/null || printf false)"
      if [[ "$app_ready" == true && "$selector_ready" == true && "$selector_interaction_ready" == true && "$engine_ready" == true && "$world_ready" == true && "$workspace_ready" == true && "$interaction_ready" == true && "$data_truth_ready" == true && "$country_truth_ready" == true && "$country_matrix_ready" == true && "$record_truth_ready" == true && "$control_plane_ready" == true && "$unified_state_ready" == true && "$assurance_ready" == true && "$research_integration_ready" == true && "$monitoring_operations_ready" == true && "$analytical_ready" == true && "$browser_reliability_ready" == true && "$performance_offline_ready" == true && "$startup_stability_ready" == true && "$bootstrap_recovery_ready" == true && "$mutation_recovery_ready" == true && "$embed_isolation_ready" == true && "$truth_ready" == true && "$health_ready" == true ]]; then
        write_receipt "verified" "GitHub, Render, the live app shell, self-hosted map engine, cartographic workspace, interaction controls, data-truth directory, global country truth, hydrated global selector, focus-safe dropdown interaction, coverage matrix, record provenance and indicator truth, Unified Analytical Workspace and Cross-View State, comparative/scenario/model assurance, research evidence/knowledge integration with preview-only human-confirmed handoffs, monitoring/digest/early-warning operations with review-gated publication, schema drift, source incidents, coverage monitoring, cross-workspace truth, five-workflow analytical directory, browser reliability contract, performance/offline contract, production-soak startup-stability contract, single-owner bootstrap contract, mutation-observer recovery contract, fixed WordPress embed-isolation contract, complete-shell browser gate, service-worker strategy, production-truth directory, runtime health, and WordPress installation gate are synchronized."
        printf 'Render release gate and live map runtime are ready for v%s at commit %s.
' "$OBSERVED_VERSION" "${OBSERVED_COMMIT:0:12}"
        printf '
SUCCESS: Site Intelligence v4.2.0 is live with Monitoring, Digests, and Early-Warning Operations.
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
