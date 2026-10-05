#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="4.50.0"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.50.0.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-v4500.XXXXXX)"
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

# Preserve dynamic production data and credentials. Certified release-bound
# registries/policies are promoted explicitly after application code.
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

ready=0
for _ in $(seq 1 60); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  case "$state" in
    healthy) ready=1; break ;;
    running) sleep 3; ready=1; break ;;
    unhealthy|exited|dead) docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;;
  esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=180 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become ready"; }

echo "=== VERIFYING $PRODUCT v$VERSION ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
from app.main import app
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest
from app.global_source_federation_v4500 import registry_manifest, source_manifest, jurisdiction_manifest, select_source, federation_plan, evaluate_trust_profile
from app.live_geospatial_event_fusion_v4490 import registry_manifest as live_registry_manifest

assert APP_VERSION == "4.50.0", APP_VERSION
assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
assert RELEASE_NAME == "Global Source Federation & Regional Authority Registry"
paths = {getattr(route, "path", None) for route in app.routes}
for required in (
    "/health", "/public/build-info", "/public/release-gate", "/public/capabilities", "/public/routes/registry",
    "/public/app/bootstrap", "/public/integrations/wordpress/bridge",
    "/public/spatial-evidence/registry", "/public/spatiotemporal/registry", "/public/spatial-graph/registry",
    "/public/live-geospatial/registry",
    "/public/source-federation/registry", "/public/source-federation/authorities",
    "/public/source-federation/authority-types", "/public/source-federation/regions",
    "/public/source-federation/select", "/public/source-federation/federate",
    "/public/source-federation/trust-profile/evaluate", "/public/source-federation/compatibility",
    "/app/{route:path}", "/v1/energy-runtime/consumer", "/v1/energy-spatial/framework",
):
    assert required in paths, required
manifest = capability_manifest(app.routes)
assert manifest["version"] == APP_VERSION
assert manifest["registry_version"] == "1.7.0", manifest["registry_version"]
assert manifest["route_count"] >= 1409, manifest["route_count"]
assert manifest["modularized_route_count"] >= 100, manifest["modularized_route_count"]
assert manifest["capability_count"] >= 21, manifest["capability_count"]
assert manifest["unclassified_route_count"] == 0, manifest["unclassified_route_count"]
family = next(item for item in manifest["capabilities"] if item["capability_id"] == "global-source-federation")
assert family["route_count"] == 10, family
assert family["modularized_route_count"] == 10, family
registry = registry_manifest()
assert registry["version"] == APP_VERSION
assert registry["source_count"] == 24
assert registry["authority_class_count"] == 10
assert registry["regional_group_count"] == 7
assert live_registry_manifest()["version"] == APP_VERSION
pse = jurisdiction_manifest("PSE")
assert {"pcbs-pxweb", "pcbs-pxweb-sdgs", "world_bank"}.issubset({row["source_id"] for row in pse["eligible_sources"]})
selection = select_source({
    "jurisdiction":"PSE",
    "concept_id":"electricity_structural_access",
    "candidates":[
        {"source_id":"world_bank","semantic_compatible":True,"freshness_state":"fresh","record_status":"final"},
        {"source_id":"pcbs-pxweb-sdgs","semantic_compatible":True,"freshness_state":"aging","record_status":"final"},
    ],
})
assert selection["selected_source_id"] == "pcbs-pxweb-sdgs", selection
trust = evaluate_trust_profile({"source_ids":["pcbs-pxweb-sdgs"],"trust_profile":{"blocked_source_ids":["pcbs-pxweb-sdgs"]}})
assert trust["authority_mutated"] is False and trust["quality_mutated"] is False
plan = federation_plan({"jurisdiction":"USA","domains":["weather","hydrology"]})
assert plan["execution"]["network_calls_performed"] is False
assert plan["execution"]["automatic_import_performed"] is False
assert {"noaa_nws","usgs-water-ogc"}.issubset({row["source_id"] for row in plan["sources"]})
print("PASS: Site Intelligence v4.50.0 global source federation and regional authority registry verified")
PYVERIFY

echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
