#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.56.0"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.56.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-v4560.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar curl; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
version_file="$(find "$TMP/package" -type f -path '*/backend/app/version.py' | head -1)"
[[ -n "$version_file" ]] || fail "backend/app/version.py missing from package"
SRC_BACKEND="$(dirname "$(dirname "$version_file")")"
grep -q 'APP_VERSION = "4.56.0"' "$version_file" || fail "package APP_VERSION mismatch"

RELEASE_BOUND_POLICIES=(
  analytical_workspace_policy_v3234.json bootstrap_recovery_policy_v32361.json briefing_publication_policy_v3290.json browser_reliability_policy_v3235.json
  comparative_model_assurance_policy_v3260.json connected_platform_policy_v300.json country_identity_registry_v43523.json embed_isolation_policy_v32363.json
  evidence_synthesis_policy_v2180.json federation_policy_v2240.json institutional_review_governance_policy_v3300.json institutional_workspaces_policy_v2220.json
  intelligence_publishing_policy_v2200.json knowledge_graph_policy_v2190.json knowledge_graph_relationship_registry_v2190.json live_intelligence_source_registry_v320.json
  map_interaction_policy_v3232.json model_governance_policy_v2170.json model_metric_registry_v2170.json monitoring_early_warning_policy_v3280.json
  mutation_observer_recovery_policy_v32362.json performance_offline_policy_v3236.json research_evidence_integration_policy_v3270.json scheduled_monitoring_policy_v2210.json
  spatial_evidence_policy_v2150.json startup_stability_policy_v32364.json unified_analytical_state_policy_v3250.json spatial_layer_registry_v4460.json
  spatiotemporal_operator_registry_v4470.json spatial_relationship_registry_v4480.json live_geospatial_event_fusion_registry_v4490.json global_source_federation_registry_v4500.json
  spatial_research_handoff_registry_v4510.json predictive_spatial_consumer_registry_v4520.json scenario_exposure_change_registry_v4530.json advanced_domain_workspace_registry_v4530.json
  reproducible_spatial_package_registry_v4540.json spatial_provenance_lineage_registry_v4550.json advanced_domain_intelligence_registry_v4552.json standalone_web_application_registry_v4553.json
  api_reliability_contract_v45531.json live_probe_consistency_registry_v455311.json standalone_functional_parity_registry_v45532.json runtime_health_domain_context_registry_v455321.json
  browser_api_transport_registry_v455322.json production_consolidation_registry_v4560.json
)
mkdir -p "$BACKUP_ROOT"
stamp="$(date +%Y%m%d-%H%M%S)"
echo "=== BACKING UP $PRODUCT BACKEND ==="
tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-backend-before-v$VERSION-$stamp.tgz" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/site-intelligence-compose-before-v$VERSION-$stamp.yml"
rsync -a --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' "$SRC_BACKEND/" "$LIVE_BACKEND/"
mkdir -p "$LIVE_BACKEND/data"
for policy in "${RELEASE_BOUND_POLICIES[@]}"; do
  [[ -f "$SRC_BACKEND/data/$policy" ]] || fail "release-bound policy missing from package: $policy"
  cp "$SRC_BACKEND/data/$policy" "$LIVE_BACKEND/data/$policy"
done
python3 - "$LIVE_BACKEND/data" "$VERSION" "${RELEASE_BOUND_POLICIES[@]}" <<'PYDATA'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); expected=sys.argv[2]; names=sys.argv[3:]
bad=[]
for name in names:
    got=json.loads((root/name).read_text(encoding='utf-8')).get('version')
    if got!=expected: bad.append((name,got))
if bad: raise SystemExit(f"release-bound policy mismatch: {bad}")
print(f"PASS: {len(names)} release-bound policies aligned to {expected}")
PYDATA
PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
[[ ! -f "$PACKAGE_ROOT/compose.yml" ]] || cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"
cd "$ROOT"
docker compose -f "$COMPOSE" config --quiet
echo "=== BUILDING $PRODUCT v$VERSION ==="
docker compose -f "$COMPOSE" build "$SERVICE"
docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"
ready=0
for _ in $(seq 1 90); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  case "$state" in healthy) ready=1; break;; unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state";; esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy"; }

echo "=== VERIFYING $PRODUCT v$VERSION CONSOLIDATION CONTRACT ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest
from app.production_consolidation_v4560 import checklist, release_snapshot
assert APP_VERSION == "4.56.0"
assert RELEASE_NAME == "Standalone Production Consolidation & Certification"
m=capability_manifest(app.routes)
assert m["registry_version"] == "2.7.0"
assert m["route_count"] == 1521
assert m["modularized_route_count"] == 212
assert m["capability_count"] == 32
assert m["unclassified_route_count"] == 0
family=next(x for x in m["capabilities"] if x["capability_id"]=="production-certification")
assert family["route_count"] == 3 and family["modularized_route_count"] == 3
result=checklist(); assert result["ok"] is True; assert result["live_runtime_asserted"] is False
snapshot=release_snapshot(); assert len(snapshot["sha256"]) == 64
print("PASS: Site Intelligence v4.56.0 standalone production consolidation contract verified")
PYVERIFY

docker exec -i "$CONTAINER" python - <<'PYCORS'
import urllib.request
req=urllib.request.Request('http://127.0.0.1:8091/health',method='OPTIONS',headers={'Origin':'https://intelligence.sustainablecatalyst.com','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'X-SCSI-Runtime-Diagnostic'})
with urllib.request.urlopen(req,timeout=10) as r:
    assert r.status==200
    assert r.headers.get('Access-Control-Allow-Origin')=='https://intelligence.sustainablecatalyst.com'
    assert 'x-scsi-runtime-diagnostic' in (r.headers.get('Access-Control-Allow-Headers') or '').lower()
print('PASS: production browser-origin CORS contract')
PYCORS

readiness_status="$(docker exec -i "$CONTAINER" python - <<'PYREADY'
import urllib.error,urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8091/ready?country=KEN',timeout=45) as r: print(r.status)
except urllib.error.HTTPError as exc: print(exc.code)
PYREADY
)"
case "$readiness_status" in 200) echo "PASS: /ready operational";; 503) echo "NOTICE: /ready truthfully reports domain-degraded/platform-unavailable; core certification continues";; *) fail "unexpected /ready HTTP status: $readiness_status";; esac

docker exec -i "$CONTAINER" python - <<'PYPROBE'
import json,urllib.request
with urllib.request.urlopen('http://127.0.0.1:8091/public/capability-health?probe=true&country=KEN',timeout=60) as r: payload=json.load(r)
assert payload['probe'] is True and len(payload['capabilities']) == 6
print('PASS: live capability-health returned six structured canonical probes')
PYPROBE

docker exec -i "$CONTAINER" python - <<'PYCERT'
import json,urllib.request
for path in ('/public/production-certification','/public/production-certification/checklist','/public/production-certification/release'):
    with urllib.request.urlopen('http://127.0.0.1:8091'+path,timeout=10) as r:
        payload=json.load(r); assert payload['version']=='4.56.0'
print('PASS: production certification API surface')
PYCERT

echo "PASS: $PRODUCT v$VERSION backend production consolidation & certification deployed."
