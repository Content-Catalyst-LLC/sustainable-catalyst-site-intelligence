#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.56.1"
PRODUCT="Site Intelligence"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-backend-v4.56.1.zip}"
ROOT="${SC_TARGET_ROOT:-/opt/sustainable-catalyst/site-intelligence}"
LIVE_BACKEND="$ROOT/backend"
COMPOSE="${SC_TARGET_COMPOSE:-$ROOT/compose.yml}"
SERVICE="${SC_TARGET_SERVICE:-site-intelligence}"
CONTAINER="${SC_TARGET_CONTAINER:-sc-site-intelligence}"
CORE_CONTAINER="${SC_CORE_CONTAINER:-sc-core}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-v4561.XXXXXX)"
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
grep -q 'APP_VERSION = "4.56.1"' "$version_file" || fail "package APP_VERSION mismatch"

mkdir -p "$BACKUP_ROOT"
stamp="$(date +%Y%m%d-%H%M%S)"
echo "=== BACKING UP $PRODUCT BACKEND + ENV ==="
tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-backend-before-v$VERSION-$stamp.tgz" backend
cp -a "$COMPOSE" "$BACKUP_ROOT/site-intelligence-compose-before-v$VERSION-$stamp.yml"
[[ ! -f "$ROOT/.env.production" ]] || cp -a "$ROOT/.env.production" "$BACKUP_ROOT/site-intelligence-env-before-v$VERSION-$stamp"

rsync -a \
  --exclude='data/' --exclude='__pycache__/' --exclude='.pytest_cache/' \
  --exclude='*.pyc' --exclude='.env' --exclude='.env.*' \
  "$SRC_BACKEND/" "$LIVE_BACKEND/"
mkdir -p "$LIVE_BACKEND/data"

python3 - "$SRC_BACKEND/data" "$LIVE_BACKEND/data" "$VERSION" <<'PYDATA'
import json, shutil, sys
from pathlib import Path
src, dst, version = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
copied=[]
for path in src.glob('*.json'):
    try: payload=json.loads(path.read_text(encoding='utf-8'))
    except Exception: continue
    if payload.get('version') == version:
        shutil.copy2(path, dst/path.name); copied.append(path.name)
if len(copied) < 47:
    raise SystemExit(f"expected at least 47 v{version} release-bound/current JSON policies, copied {len(copied)}")
print(f"PASS: copied {len(copied)} v{version} release-bound/current policies")
PYDATA

PACKAGE_ROOT="$(dirname "$SRC_BACKEND")"
[[ ! -f "$PACKAGE_ROOT/compose.yml" ]] || cp "$PACKAGE_ROOT/compose.yml" "$COMPOSE"

ENV_FILE="$ROOT/.env.production"
touch "$ENV_FILE"
python3 - "$ENV_FILE" <<'PYENV'
from pathlib import Path
import sys
path=Path(sys.argv[1])
updates={
 "SC_SI_PLATFORM_CORE_ENABLED":"true",
 "SC_SI_PLATFORM_CORE_URL":"http://sc-core:8090",
 "SC_SI_PLATFORM_CORE_INTERNAL_READS":"true",
 "SC_SI_INTERNATIONAL_LAW_OBSERVATORY_ENABLED":"true",
 "SC_SI_ECONOMICS_SUSTAINABILITY_ENABLED":"true",
 "SC_SI_SCIENTIFIC_EARTH_SYSTEMS_ENABLED":"true",
 "SC_SI_HUMANITARIAN_CONFLICT_DISPLACEMENT_ENABLED":"true",
 "SC_SI_TRADE_ENERGY_RESOURCE_SECURITY_ENABLED":"true",
 "SC_SI_UNIFIED_DOSSIERS_ENABLED":"true",
}
lines=path.read_text(encoding='utf-8').splitlines() if path.exists() else []
out=[]; seen=set()
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        key=line.split('=',1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}"); seen.add(key); continue
    out.append(line)
for key,value in updates.items():
    if key not in seen: out.append(f"{key}={value}")
path.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
print('PASS: Site Intelligence Core bridge environment activated')
PYENV

# Core owns the source/connector catalog. Re-run its idempotent migration/seed path
# so source definitions cannot silently disappear from the production DB.
docker inspect "$CORE_CONTAINER" >/dev/null 2>&1 || fail "$CORE_CONTAINER is required for v4.56.1 Core bridge activation"
echo "=== RESEEDING / AUDITING PLATFORM CORE SOURCE CATALOG ==="
docker exec -i "$CORE_CONTAINER" python - <<'PYCORE'
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
settings=Settings.from_env(); db=Database(settings.database_url)
run_migrations(db)
status=migration_status(db)
sources=int(status.get('live_data_sources') or 0)
connectors=int(status.get('live_data_connectors') or 0)
assert sources >= 40, status
assert connectors >= 39, status
print(f"PASS: Platform Core catalog sources={sources} connectors={connectors}")
PYCORE

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

echo "=== VERIFYING v4.56.1 ROUTE / BRIDGE CONTRACT ==="
docker exec -i "$CONTAINER" python - <<'PYVERIFY'
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest
assert APP_VERSION == '4.56.1'
assert RELEASE_NAME == 'Platform Core International Law Bridge & Connector Activation'
m=capability_manifest(app.routes)
assert m['registry_version']=='2.8.0', m
assert m['route_count']==1525, m
assert m['modularized_route_count']==216, m
assert m['capability_count']==33, m
assert m['unclassified_route_count']==0, m
family=next(x for x in m['capabilities'] if x['capability_id']=='core-domain-bridge')
assert family['route_count']==4 and family['modularized_route_count']==4
print('PASS: Site Intelligence v4.56.1 route and capability contract')
PYVERIFY

echo "=== VERIFYING CORE CATALOG THROUGH SITE INTELLIGENCE ==="
docker exec -i "$CONTAINER" python - <<'PYCAT'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8091/public/core-domain-bridge/sources',timeout=30) as r: payload=json.load(r)
assert payload['ok'] is True, payload
assert payload['state']=='connected', payload
assert payload['read_mode']=='private-core-read', payload
assert int(payload['source_count']) >= 40, payload
assert int(payload['connector_count']) >= 39, payload
assert payload['credential_exposed'] is False
print(f"PASS: Site Intelligence sees Core sources={payload['source_count']} connectors={payload['connector_count']}")
PYCAT

echo "=== VERIFYING SIX CANONICAL CORE-BACKED WORKSPACES ==="
docker exec -i "$CONTAINER" python - <<'PYDOMAINS'
import json, urllib.request
url='http://127.0.0.1:8091/public/core-domain-bridge/diagnostics?probe=true&country=KEN'
with urllib.request.urlopen(url,timeout=120) as r: payload=json.load(r)
assert payload['ok'] is True, payload
assert payload['catalog']['minimum_source_target_met'] is True, payload
assert payload['catalog']['minimum_connector_target_met'] is True, payload
assert set(payload['domains']) == {'law','economics','humanitarian','science','resources','dossiers'}, payload
assert payload.get('probe_ok') is True, payload.get('capability_probes')
for row in payload['capability_probes']:
    assert int(row['http_status']) < 500, row
print('PASS: law/economics/humanitarian/science/resources/dossiers bridge probes are operational')
PYDOMAINS

echo "=== VERIFYING PUBLIC-SAFE BRIDGE ENDPOINTS ==="
for path in \
  /public/core-domain-bridge \
  /public/core-domain-bridge/sources \
  /public/core-domain-bridge/domains/law \
  /public/core-domain-bridge/domains/economics \
  /public/core-domain-bridge/domains/humanitarian \
  /public/core-domain-bridge/domains/science \
  /public/core-domain-bridge/domains/resources \
  /public/core-domain-bridge/domains/dossiers; do
  curl -fsS "http://127.0.0.1:8091$path" >/dev/null || fail "failed: $path"
done

echo "PASS: $PRODUCT v$VERSION backend Platform Core cross-domain bridge deployed and certified."
