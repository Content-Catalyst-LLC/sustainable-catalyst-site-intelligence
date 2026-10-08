#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="4.55.3.1"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.55.3.1.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-v45531.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
version_file="$(find "$TMP/package" -type f -path '*/backend/app/version.py' | head -1)"
[[ -n "$version_file" ]] || fail "backend/app/version.py missing from package"
SRC_BACKEND="$(dirname "$(dirname "$version_file")")"
grep -q "APP_VERSION = \"$VERSION\"" "$version_file" || fail "package APP_VERSION mismatch"

RELEASE_BOUND_POLICIES=(
  analytical_workspace_policy_v3234.json
  bootstrap_recovery_policy_v32361.json
  briefing_publication_policy_v3290.json
  browser_reliability_policy_v3235.json
  comparative_model_assurance_policy_v3260.json
  connected_platform_policy_v300.json
  country_identity_registry_v43523.json
  embed_isolation_policy_v32363.json
  evidence_synthesis_policy_v2180.json
  federation_policy_v2240.json
  institutional_review_governance_policy_v3300.json
  institutional_workspaces_policy_v2220.json
  intelligence_publishing_policy_v2200.json
  knowledge_graph_policy_v2190.json
  knowledge_graph_relationship_registry_v2190.json
  live_intelligence_source_registry_v320.json
  map_interaction_policy_v3232.json
  model_governance_policy_v2170.json
  model_metric_registry_v2170.json
  monitoring_early_warning_policy_v3280.json
  mutation_observer_recovery_policy_v32362.json
  performance_offline_policy_v3236.json
  research_evidence_integration_policy_v3270.json
  scheduled_monitoring_policy_v2210.json
  spatial_evidence_policy_v2150.json
  startup_stability_policy_v32364.json
  unified_analytical_state_policy_v3250.json
  spatial_layer_registry_v4460.json
  spatiotemporal_operator_registry_v4470.json
  spatial_relationship_registry_v4480.json
  live_geospatial_event_fusion_registry_v4490.json
  global_source_federation_registry_v4500.json
  spatial_research_handoff_registry_v4510.json
  predictive_spatial_consumer_registry_v4520.json
  scenario_exposure_change_registry_v4530.json
  advanced_domain_workspace_registry_v4530.json
  reproducible_spatial_package_registry_v4540.json
  spatial_provenance_lineage_registry_v4550.json
  advanced_domain_intelligence_registry_v4552.json
  standalone_web_application_registry_v4553.json
  api_reliability_contract_v45531.json
)

if [[ ! -d "$BACKUP_ROOT" ]]; then
  if mkdir -p "$BACKUP_ROOT" 2>/dev/null; then :; else
    command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo is unavailable"
    sudo install -d -o "$(id -un)" -g "$(id -gn)" -m 750 "$BACKUP_ROOT"
  fi
fi
if [[ ! -w "$BACKUP_ROOT" ]]; then
  command -v sudo >/dev/null || fail "$BACKUP_ROOT is unwritable and sudo is unavailable"
  sudo chown "$(id -un):$(id -gn)" "$BACKUP_ROOT"
  sudo chmod 750 "$BACKUP_ROOT"
fi

stamp="$(date +%Y%m%d-%H%M%S)"
echo "=== BACKING UP $PRODUCT BACKEND ==="
tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-backend-before-v$VERSION-$stamp.tgz" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/site-intelligence-compose-before-v$VERSION-$stamp.yml"

# Preserve dynamic production data and credentials. Release-bound registries
# and policies are promoted explicitly after application code.
rsync -a \
  --exclude='data/' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='.env.*' \
  "$SRC_BACKEND/" "$LIVE_BACKEND/"

mkdir -p "$LIVE_BACKEND/data"
for policy in "${RELEASE_BOUND_POLICIES[@]}"; do
  [[ -f "$SRC_BACKEND/data/$policy" ]] || fail "release-bound policy missing from package: $policy"
  cp "$SRC_BACKEND/data/$policy" "$LIVE_BACKEND/data/$policy"
done

python3 - "$LIVE_BACKEND/data" "$VERSION" "${RELEASE_BOUND_POLICIES[@]}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); expected=sys.argv[2]; names=sys.argv[3:]
bad=[]
for name in names:
    version=json.loads((root/name).read_text(encoding='utf-8')).get('version')
    if version != expected:
        bad.append((name, version))
if bad:
    raise SystemExit(f"release-bound policy mismatch: {bad}")
print(f"PASS: {len(names)} release-bound policies aligned to {expected}")
PY

PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
if [[ -f "$PACKAGE_ROOT/compose.yml" ]]; then
  cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"
fi

cd "$ROOT"
docker compose -f "$COMPOSE" config --quiet
echo "=== BUILDING $PRODUCT v$VERSION ==="
docker compose -f "$COMPOSE" build "$SERVICE"
docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"

# A container that is merely running is not considered ready when Docker has
# a health check. This avoids issuing verification curls during Uvicorn startup.
ready=0
for _ in $(seq 1 90); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  case "$state" in
    healthy) ready=1; break ;;
    running)
      if docker inspect --format '{{if .State.Health}}yes{{else}}no{{end}}' "$CONTAINER" 2>/dev/null | grep -q '^no$'; then
        if docker exec "$CONTAINER" python - <<'PY' >/dev/null 2>&1
import urllib.request
with urllib.request.urlopen('http://127.0.0.1:8091/health', timeout=3) as r:
    assert r.status == 200
PY
        then ready=1; break; fi
      fi
      ;;
    unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;;
  esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become healthy/ready"; }

echo "=== VERIFYING $PRODUCT v$VERSION ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
from app.main import app
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.api_reliability_v45531 import api_contract_truth_manifest, normalize_reliable_payload
from app.config import get_settings

assert APP_VERSION == "4.55.3.1", APP_VERSION
assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
assert RELEASE_NAME == "API Reliability & Contract Truth Repair"
paths={getattr(route,"path",None) for route in app.routes}
for required in (
    "/health", "/ready", "/public/api-contract-truth", "/public/capability-health",
    "/public/reliable/economics/records", "/public/reliable/law/records",
    "/public/reliable/science/records", "/public/reliable/humanitarian/records",
    "/public/reliable/resources/records", "/public/reliable/dossiers/country",
    "/public/web-app/manifest", "/public/release-gate"):
    assert required in paths, required
m=capability_manifest(app.routes)
assert m["registry_version"] == "2.5.0"
assert m["route_count"] == 1515
assert m["modularized_route_count"] == 206
assert m["capability_count"] == 30
assert m["unclassified_route_count"] == 0
family=next(x for x in m["capabilities"] if x["capability_id"]=="api-reliability")
assert family["route_count"]==9 and family["modularized_route_count"]==9 and family["maturity"]=="production"
legacy=[x for x in m["capabilities"] if x["owner"]=="backend.app.main"]
assert legacy and all(x["maturity"]=="migration" for x in legacy)
keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
assert len(keys)==len(set(keys))
truth=api_contract_truth_manifest()
assert truth["canonical_routes"]["readiness"]=="/ready"
connected_empty={"ok":True,"integration":{"state":"connected"},"records":[]}
out,status=normalize_reliable_payload(connected_empty,capability="economics")
assert status==200 and out["ok"] is True and out["data_state"]=="no-records"
failed={"ok":True,"integration":{"state":"degraded","message":"unreachable"},"records":[]}
out,status=normalize_reliable_payload(failed,capability="economics")
assert status==503 and out["ok"] is False and out["legacy_ok"] is True
assert "https://intelligence.sustainablecatalyst.com" in get_settings().cors_origin_list
print("PASS: Site Intelligence v4.55.3.1 API reliability and contract truth verified")
PYVERIFY

# Readiness is deliberately allowed to return 503: the release must deploy so it
# can truthfully report an unavailable required dependency. Production data-ready
# certification requires HTTP 200 and explicit live capability checks.
readiness_status="$(docker exec "$CONTAINER" python - <<'PYREADY'
import urllib.error, urllib.request
url='http://127.0.0.1:8091/ready'
try:
    with urllib.request.urlopen(url, timeout=8) as r:
        print(r.status)
except urllib.error.HTTPError as exc:
    print(exc.code)
PYREADY
)"
case "$readiness_status" in
  200) echo "PASS: /ready reports required data dependencies ready" ;;
  503) echo "NOTICE: /ready reports data dependencies NOT READY; deployment is truthful but data-ready certification is withheld" ;;
  *) fail "unexpected /ready HTTP status: $readiness_status" ;;
esac

echo "PASS: $PRODUCT v$VERSION backend deployed and contract-verified."
