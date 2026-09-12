#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="4.40.0.1"
TARGET_KEY="site-intelligence"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.40.0.1.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
PORT="${SC_TARGET_PORT:-8091}"
PUBLIC_BASE="${SC_SITE_INTELLIGENCE_PUBLIC_BASE:-https://site-intelligence-api.sustainablecatalyst.com}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-v44001.XXXXXX)"
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
version_file="$(find "$TMP/package" -type f -path '*/backend/app/version.py' | head -1)"
[[ -n "$version_file" ]] || fail "backend/app/version.py missing from package"
SRC_BACKEND="$(dirname "$(dirname "$version_file")")"
grep -q "APP_VERSION = \"$VERSION\"" "$version_file" || fail "package APP_VERSION mismatch"
grep -q "CONSUMER_VERSION = '4.40.0'" "$SRC_BACKEND/app/energy_runtime_consumer.py" || fail "preserved Energy Systems consumer version mismatch"
grep -q "registered_source_count=len(LIVE_INTELLIGENCE_FEED_REGISTRY)" "$SRC_BACKEND/app/main.py" || fail "runtime metric binding missing"
grep -q "configure" "$SRC_BACKEND/app/homepage_summary_v4390.py" >/dev/null 2>&1 || true

python3 - "$SRC_BACKEND" "$VERSION" "${STATIC_RELEASE_FILES[@]}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); version=sys.argv[2]; names=sys.argv[3:]
assert len(names)==27, len(names)
for name in names:
    p=root/'data'/name
    if not p.is_file(): raise SystemExit(f"missing static release file: {name}")
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
BACKUP="$BACKUP_ROOT/site-intelligence-before-v${VERSION}-${stamp}.tgz"
echo "=== BACKING UP $PRODUCT ==="
tar -C "$ROOT" -czf "$BACKUP" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/site-intelligence-compose-before-v${VERSION}-${stamp}.yml"
echo "Backup: $BACKUP"

# Overlay executable code while protecting runtime state.
rsync -a \
  --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' --exclude='*.pyc' \
  --exclude='.env' --exclude='.env.*' \
  "$SRC_BACKEND/" "$LIVE_BACKEND/"

# Update only the explicit immutable release-bound registry/policy allowlist.
echo "=== RECONCILING RELEASE-BOUND STATIC DATA ==="
mkdir -p "$LIVE_BACKEND/data"
for name in "${STATIC_RELEASE_FILES[@]}"; do
  install -m 0644 "$SRC_BACKEND/data/$name" "$LIVE_BACKEND/data/$name"
done

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
    unhealthy|exited|dead) docker logs --tail=220 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state" ;;
  esac
  sleep 2
done
[[ "$ready" == 1 ]] || { docker logs --tail=220 "$CONTAINER" >&2 || true; fail "$CONTAINER did not become ready"; }

echo "=== VERIFYING APPLICATION CONTRACT ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME
from app.live_intelligence_reliability_v361 import FEED_REGISTRY, DEFAULT_FEEDS
from app.homepage_summary_v4390 import build_homepage_summary
from app.main import app
assert APP_VERSION == '4.40.0.1'
assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
assert RELEASE_NAME == 'Homepage Live Intelligence Runtime Repair'
from app.energy_runtime_consumer import framework
assert framework()['consumer_version'] == '4.40.0'
summary = build_homepage_summary(
    {'signals': [{'signal_id':'test','label':'test','value':'1','source_name':'test'}], 'gateway':{}},
    registered_source_count=len(FEED_REGISTRY),
    enabled_source_count=len(DEFAULT_FEEDS),
)
metrics={x['id']:x['value'] for x in summary['metrics']}
assert metrics['registered_sources'] == len(FEED_REGISTRY)
assert metrics['enabled_sources'] == len(DEFAULT_FEEDS)
assert metrics['current_signals'] == 1
paths={getattr(r,'path',None) for r in app.routes}
assert '/v1/public/site-intelligence/summary' in paths
assert '/public/live-intelligence/status' in paths
print('PASS: v4.40.0.1 runtime registry and homepage summary are aligned')
print('registered_feeds:', len(FEED_REGISTRY))
print('enabled_by_default:', len(DEFAULT_FEEDS))
PYVERIFY

echo "=== LOCAL HEALTH ==="
health="$(curl -fsS "http://127.0.0.1:${PORT}/health")"
python3 - "$health" <<'PY'
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('version')=='4.40.0.1', x
print('PASS: local health reports Site Intelligence 4.40.0.1')
PY

echo "=== LOCAL HOMEPAGE SUMMARY ==="
summary="$(curl -fsS "http://127.0.0.1:${PORT}/v1/public/site-intelligence/summary")"
python3 - "$summary" <<'PY'
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('version')=='4.40.0.1', x
m={str(v.get('id')):v.get('value') for v in x.get('metrics',[]) if isinstance(v,dict)}
for key in ('country_profiles','registered_sources','enabled_sources','current_signals'):
    assert key in m, (key,m)
    assert isinstance(m[key], int) and m[key] >= 0, (key,m[key])
assert m['country_profiles'] > 0, m
print('PASS: local homepage summary exposes four numeric canonical metrics')
print(json.dumps(m,indent=2))
PY

echo "=== LOCAL RELEASE GATE ==="
gate="$(curl -fsS "http://127.0.0.1:${PORT}/public/release-gate?plugin_version=4.40.0.1&expected_release_id=site-intelligence-v4.40.0.1")"
python3 - "$gate" <<'PY'
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('install_allowed') is True; assert x.get('version')=='4.40.0.1', x
print('PASS: local release gate allows WordPress 4.40.0.1')
PY

if [[ "${SC_SKIP_PUBLIC_VERIFY:-0}" != "1" ]]; then
  echo "=== PUBLIC BACKEND HEALTH ==="
  public_health=""
  for _ in $(seq 1 20); do
    public_health="$(curl -fsS --max-time 15 "$PUBLIC_BASE/health" 2>/dev/null || true)"
    if python3 - "$public_health" <<'PY' >/dev/null 2>&1
import json,sys
x=json.loads(sys.argv[1]); raise SystemExit(0 if x.get('version')=='4.40.0.1' else 1)
PY
    then break; fi
    sleep 3
  done
  python3 - "$public_health" <<'PY'
import json,sys
x=json.loads(sys.argv[1]); assert x.get('ok') is True; assert x.get('version')=='4.40.0.1', x
print('PASS: public backend health reports 4.40.0.1')
PY

  echo "=== PUBLIC HOMEPAGE SUMMARY ==="
  public_summary="$(curl -fsS --max-time 30 "$PUBLIC_BASE/v1/public/site-intelligence/summary")"
  python3 - "$public_summary" <<'PY'
import json,sys
x=json.loads(sys.argv[1]); assert x.get('version')=='4.40.0.1', x
m={str(v.get('id')):v.get('value') for v in x.get('metrics',[]) if isinstance(v,dict)}
for key in ('country_profiles','registered_sources','enabled_sources','current_signals'):
    assert isinstance(m.get(key),int) and m[key] >= 0, (key,m)
print('PASS: public homepage summary exposes numeric canonical metrics')
print(json.dumps(m,indent=2))
PY
fi

echo "PASS: $PRODUCT v$VERSION backend deployed and verified."
echo "Backup: $BACKUP"
echo "NEXT: install the v$VERSION WordPress plugin, clear caches, then complete browser ticker acceptance."
