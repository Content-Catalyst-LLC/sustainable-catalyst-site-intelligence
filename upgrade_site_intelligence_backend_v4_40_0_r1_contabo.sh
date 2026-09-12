#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="4.40.0"
REVISION="r1"
TARGET_KEY="site-intelligence"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.40.0-r1.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
PORT="${SC_TARGET_PORT:-8091}"
BACKUP_ROOT="/opt/sustainable-catalyst/backups"
TMP="$(mktemp -d /tmp/sc-site-v4400-r1.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

STATIC_RELEASE_FILES=(
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
)

fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker python3 tar curl; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "backend package not found: $ARCHIVE"
[[ -d "$ROOT" && -d "$LIVE_BACKEND" ]] || fail "runtime root/backend missing: $ROOT"
[[ -f "$COMPOSE" ]] || fail "Compose file not found: $COMPOSE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid backend ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
consumer="$(find "$TMP/package" -type f -path '*/backend/app/energy_runtime_consumer.py' | head -1)"
[[ -n "$consumer" ]] || fail "energy runtime consumer missing from package"
SRC_BACKEND="$(dirname "$(dirname "$consumer")")"
grep -q "CONSUMER_VERSION = '$VERSION'" "$consumer" || fail "package consumer version mismatch"
grep -q "TARGET_KEY = '$TARGET_KEY'" "$consumer" || fail "package target mismatch"
grep -q "APP_VERSION = \"$VERSION\"" "$SRC_BACKEND/app/version.py" || fail "package APP_VERSION mismatch"

python3 - "$SRC_BACKEND" "$VERSION" "${STATIC_RELEASE_FILES[@]}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); version=sys.argv[2]; names=sys.argv[3:]
assert len(names)==27, len(names)
for name in names:
    p=root/'data'/name
    if not p.is_file():
        raise SystemExit(f"missing static release file: {name}")
    payload=json.loads(p.read_text(encoding='utf-8'))
    if payload.get('version') != version:
        raise SystemExit(f"{name}: version {payload.get('version')!r} != {version!r}")
print(f"PASS: {len(names)} release-bound static files identify Site Intelligence {version}")
PY

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
BACKUP="$BACKUP_ROOT/site-intelligence-before-v${VERSION}-${REVISION}-${stamp}.tgz"
echo "=== BACKING UP $PRODUCT ==="
tar -C "$ROOT" -czf "$BACKUP" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/site-intelligence-compose-before-v${VERSION}-${REVISION}-${stamp}.yml"
echo "Backup: $BACKUP"

# Overlay executable code while protecting mutable runtime state.
rsync -a \
  --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' \
  --exclude='.env' --exclude='.env.*' \
  "$SRC_BACKEND/" "$LIVE_BACKEND/"

# Reconcile only the explicit release-bound immutable policy/registry allowlist.
# JSONL files, runtime state directories, caches, and user/service data remain untouched.
echo "=== RECONCILING RELEASE-BOUND STATIC DATA ==="
mkdir -p "$LIVE_BACKEND/data"
for name in "${STATIC_RELEASE_FILES[@]}"; do
  install -m 0644 "$SRC_BACKEND/data/$name" "$LIVE_BACKEND/data/$name"
done

python3 - "$LIVE_BACKEND" "$VERSION" "${STATIC_RELEASE_FILES[@]}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); version=sys.argv[2]; names=sys.argv[3:]
for name in names:
    payload=json.loads((root/'data'/name).read_text(encoding='utf-8'))
    assert payload.get('version') == version, (name, payload.get('version'))
print(f"PASS: live source tree reconciled for {len(names)} static files")
PY

cd "$ROOT"
docker compose -f "$COMPOSE" config --quiet
echo "=== BUILDING $PRODUCT v$VERSION ($REVISION) ==="
docker compose -f "$COMPOSE" build "$SERVICE"
docker compose -f "$COMPOSE" up -d --force-recreate "$SERVICE"

ready=0
for _ in $(seq 1 60); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  case "$state" in
    healthy) ready=1; break ;;
    running) sleep 3; ready=1; break ;;
    unhealthy|exited|dead) docker logs --tail=220 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;;
  esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=220 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become ready"; }

echo "=== VERIFYING APPLICATION IMPORT + STATIC POLICY ALIGNMENT ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
import json
from pathlib import Path
from app.version import APP_VERSION
from app.main import app
from app.energy_runtime_consumer import framework
assert APP_VERSION == '4.40.0'
f=framework()
assert f['consumer_version']=='4.40.0'
assert f['target_key']=='site-intelligence'
paths={getattr(r,'path',None) for r in app.routes}
assert '/v1/energy-runtime/consumer' in paths
assert '/v1/energy-runtime/consume' in paths
p=Path('/app/backend/data/monitoring_early_warning_policy_v3280.json')
if not p.exists(): p=Path('/app/data/monitoring_early_warning_policy_v3280.json')
payload=json.loads(p.read_text(encoding='utf-8'))
assert payload['version']=='4.40.0'
print('PASS: app.main imports and v4.40.0 runtime consumer is active')
print('PASS: monitoring policy compatibility marker is 4.40.0')
PYVERIFY

echo "=== LOCAL HEALTH ==="
health="$(curl -fsS "http://127.0.0.1:${PORT}/health")"
python3 - <<'PY' "$health"
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('version')=='4.40.0', x
print('PASS: local health reports Site Intelligence 4.40.0')
PY

echo "=== LOCAL RELEASE GATE ==="
gate="$(curl -fsS "http://127.0.0.1:${PORT}/public/release-gate?plugin_version=4.40.0&expected_release_id=site-intelligence-v4.40.0")"
python3 - <<'PY' "$gate"
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('install_allowed') is True; assert x.get('version')=='4.40.0', x
print('PASS: local release gate allows WordPress 4.40.0')
PY

echo "PASS: $PRODUCT v$VERSION source reconciliation $REVISION deployed and verified."
echo "Backup: $BACKUP"
