#!/usr/bin/env bash
set -euo pipefail
RELEASE="4.35.15"
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
  python3 - "$DEPLOYMENT_RECEIPT" "$RELEASE" "$RELEASE_ID" "$REPO_SLUG" "$BRANCH" "$COMMIT" "$PREVIOUS_COMMIT" "$ROLLBACK_TAG" "$TRIGGERED" "$state" "$message" <<'PY'
from datetime import datetime,timezone
from pathlib import Path
import json,sys
(path,version,release_id,repo,branch,commit,previous,rollback,trigger,state,message)=sys.argv[1:]
payload={"schema":"sc-site-intelligence-deployment-receipt/1.1","version":version,"release_id":release_id,"repository":repo,"branch":branch,"commit":commit or None,"previous_commit":previous or None,"rollback_tag":rollback,"deployment_trigger":trigger,"state":state,"message":message or None,"verification_policy":"first-party-release-identity-and-runtime; external-source-health-non-blocking","updated_at":datetime.now(timezone.utc).isoformat()}
Path(path).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
PY
}
fail(){ write_receipt "failed" "${1:-unknown failure}"; printf '\nERROR: %s\n' "$1" >&2; exit 1; }
for command in git curl python3 rsync; do command -v "$command" >/dev/null 2>&1 || fail "$command is required."; done

printf '\n==> Validating release source before promotion\n'
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then SC_SI_STRICT_DEPENDENCIES=1 SC_SI_SKIP_BROWSER=1 PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$SOURCE_ROOT/verify_site_intelligence_v4_35_10_macos.sh"; else SC_SI_SKIP_BROWSER=1 bash "$SOURCE_ROOT/verify_site_intelligence_v4_35_10_macos.sh"; fi

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
if [[ -x "$SOURCE_ROOT/.venv/bin/python" ]]; then SC_SI_STRICT_DEPENDENCIES=1 SC_SI_SKIP_BROWSER=1 PYTHON="$SOURCE_ROOT/.venv/bin/python" bash "$CLONE_ROOT/verify_site_intelligence_v4_35_10_macos.sh"; else SC_SI_SKIP_BROWSER=1 bash "$CLONE_ROOT/verify_site_intelligence_v4_35_10_macos.sh"; fi
cd "$CLONE_ROOT"
find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
git add -A
if ! git diff --cached --quiet; then
  git config user.name >/dev/null 2>&1 || fail 'Git user.name is not configured.'
  git config user.email >/dev/null 2>&1 || fail 'Git user.email is not configured.'
  git commit -m "Site Intelligence v${RELEASE} — Authoritative Connector Expansion IV"
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

printf '\n==> Verifying Render deployment identity and first-party runtime\n'
ATTEMPTS="${SC_SI_RENDER_VERIFY_ATTEMPTS:-24}"; INTERVAL="${SC_SI_RENDER_VERIFY_INTERVAL_SECONDS:-10}"
OBSERVED_VERSION=unavailable; OBSERVED_COMMIT=unavailable; OBSERVED_GATE=unavailable; OBSERVED_RELEASE_ID=unavailable
for ((attempt=1; attempt<=ATTEMPTS; attempt++)); do
  gate_url="${RENDER_URL%/}/public/release-gate?plugin_version=${RELEASE}&expected_commit=${COMMIT}&expected_release_id=${RELEASE_ID}&cache_bust=${attempt}"
  gate="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' -H 'Pragma: no-cache' "$gate_url" 2>/dev/null || true)"
  if [[ -n "$gate" ]]; then
    read -r OBSERVED_VERSION OBSERVED_COMMIT OBSERVED_RELEASE_ID OBSERVED_GATE < <(python3 -c 'import json,sys;d=json.load(sys.stdin);dep=d.get("deployment",{});print(d.get("backend_version",d.get("version","unavailable")),dep.get("git_commit","unavailable"),d.get("release_id","unavailable"),"ready" if d.get("install_allowed") else d.get("gate_state","blocked"))' <<<"$gate" 2>/dev/null || printf 'unavailable unavailable unavailable unavailable\n')
    printf 'Render check %d/%d: version=%s gate=%s commit=%s\n' "$attempt" "$ATTEMPTS" "$OBSERVED_VERSION" "$OBSERVED_GATE" "${OBSERVED_COMMIT:0:12}"
    if [[ "$OBSERVED_VERSION" == "$RELEASE" && "$OBSERVED_RELEASE_ID" == "$RELEASE_ID" && "$OBSERVED_GATE" == "ready" && ( "$OBSERVED_COMMIT" == "$COMMIT" || "$COMMIT" == "$OBSERVED_COMMIT"* || "$OBSERVED_COMMIT" == "$COMMIT"* ) ]]; then
      health="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/health?verify=${attempt}" 2>/dev/null || true)"
      runtime="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/runtime-health?verify=${attempt}" 2>/dev/null || true)"
      deployment="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/deployment-verification?verify=${attempt}" 2>/dev/null || true)"
      v4="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/v4/readiness?verify=${attempt}" 2>/dev/null || true)"
      connectors="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/authoritative-connectors/readiness?verify=${attempt}" 2>/dev/null || true)"
      evidence="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/evidence-intelligence/readiness?verify=${attempt}" 2>/dev/null || true)"
      workspace_evidence="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/workspace-evidence/readiness?verify=${attempt}" 2>/dev/null || true)"
      production_audit="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/authoritative-apis/production-readiness?verify=${attempt}" 2>/dev/null || true)"
      source_health="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/public/source-health-policy?verify=${attempt}" 2>/dev/null || true)"
      app_html="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/?release=${RELEASE}&verify=${attempt}" 2>/dev/null || true)"
      app_js="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/app.js?verify=${attempt}" 2>/dev/null || true)"
      app_css="$(curl -fsS --connect-timeout 3 --max-time 8 -H 'Cache-Control: no-cache, no-store' "${RENDER_URL%/}/app/assets/app.css?verify=${attempt}" 2>/dev/null || true)"
      health_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] else "false")' "$RELEASE" <<<"$health" 2>/dev/null || printf false)"
      runtime_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("live_upstream_checks_performed") is False else "false")' "$RELEASE" <<<"$runtime" 2>/dev/null || printf false)"
      deployment_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("source_health_blocks_release") is False and all(d.get("checks",{}).values()) else "false")' "$RELEASE" <<<"$deployment" 2>/dev/null || printf false)"
      v4_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("summary",{}).get("preserved_routes")==35 else "false")' "$RELEASE" <<<"$v4" 2>/dev/null || printf false)"
      connector_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("network_calls_performed") is False else "false")' "$RELEASE" <<<"$connectors" 2>/dev/null || printf false)"
      evidence_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("network_calls_performed") is False else "false")' "$RELEASE" <<<"$evidence" 2>/dev/null || printf false)"
      workspace_evidence_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("network_calls_performed") is False and all(d.get("checks",{}).values()) else "false")' "$RELEASE" <<<"$workspace_evidence" 2>/dev/null || printf false)"
      production_audit_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("network_calls_performed") is False else "false")' "$RELEASE" <<<"$production_audit" 2>/dev/null || printf false)"
      source_health_ready="$(python3 -c 'import json,sys;d=json.load(sys.stdin);print("true" if d.get("ok") and d.get("version")==sys.argv[1] and d.get("network_calls_performed") is False and d.get("summary",{}).get("release_blocking_sources")==0 else "false")' "$RELEASE" <<<"$source_health" 2>/dev/null || printf false)"
      app_ready=false
      if [[ "$app_html" == *"v=${RELEASE}"* && "$app_js" == *"const APP_VERSION=\"${RELEASE}\""* && -n "$app_css" ]]; then app_ready=true; fi
      printf 'Release verification: health=%s runtime=%s deployment=%s routes=%s connectors=%s evidence=%s workspace-evidence=%s production-audit=%s source-policy=%s app=%s\n' "$health_ready" "$runtime_ready" "$deployment_ready" "$v4_ready" "$connector_ready" "$evidence_ready" "$workspace_evidence_ready" "$production_audit_ready" "$source_health_ready" "$app_ready"
      if [[ "$health_ready" == true && "$runtime_ready" == true && "$deployment_ready" == true && "$v4_ready" == true && "$connector_ready" == true && "$evidence_ready" == true && "$workspace_evidence_ready" == true && "$production_audit_ready" == true && "$source_health_ready" == true && "$app_ready" == true ]]; then
        source_summary="$(python3 -c 'import json,sys;d=json.load(sys.stdin);s=d.get("summary",{});print(f"configured={s.get('"'"'configured'"'"',0)} configuration-required={s.get('"'"'configuration_required'"'"',0)} release-blocking={s.get('"'"'release_blocking_sources'"'"',0)}")' <<<"$source_health" 2>/dev/null || printf 'unavailable')"
        printf 'Operational source policy: %s (non-blocking; no upstream probes in release verification)\n' "$source_summary"
        write_receipt "verified" "Release identity, first-party application/runtime, 35-route platform contract, authoritative connector contract, canonical workspace-evidence contract, and non-blocking source-health policy are synchronized. External source availability is intentionally excluded from the release decision."
        printf '\nSUCCESS: Site Intelligence v%s is live with Authoritative Connector Expansion IV at commit %s.\nDeployment receipt: %s\nRollback tag: %s (%s)\n' "$RELEASE" "${OBSERVED_COMMIT:0:12}" "$DEPLOYMENT_RECEIPT" "$ROLLBACK_TAG" "${PREVIOUS_COMMIT:0:12}"
        exit 0
      fi
    fi
  fi
  sleep "$INTERVAL"
done
fail "GitHub is current, but Render did not verify the first-party v${RELEASE}/${RELEASE_ID} deployment at commit ${COMMIT}. External source health was not used as a blocker. Rerun this installer to resume verification without creating a new rollback point."
