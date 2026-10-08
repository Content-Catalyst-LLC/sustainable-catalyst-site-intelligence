#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.56.0"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-web-v4.56.0.zip}"
ROOT="${SC_WEB_ROOT:-/opt/sustainable-catalyst/site-intelligence-web}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
CONTAINER="${SC_WEB_CONTAINER:-sc-site-intelligence-web}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-web-v4560.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker curl grep tar; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "web package not found: $ARCHIVE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid web ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
WEB_ROOT="$(find "$TMP/package" -type f -name index.html -path '*/web/index.html' -print -quit | xargs -r dirname)"
[[ -n "$WEB_ROOT" && -f "$WEB_ROOT/config.js" && -f "$WEB_ROOT/compose.yml" ]] || fail "web package layout invalid"
grep -q 'release: "4.56.0"' "$WEB_ROOT/config.js" || fail "web release mismatch"
grep -q 'runtimeMode: "standalone-production-certified"' "$WEB_ROOT/config.js" || fail "production-certified runtime mode missing"
grep -q 'id="primaryNavigation"' "$WEB_ROOT/index.html" || fail "functional navigation missing"
grep -q 'standalone-api-bridge-v45532.js' "$WEB_ROOT/index.html" || fail "standalone API bridge missing"
grep -q '127.0.0.1:8096:80' "$WEB_ROOT/compose.yml" || fail "web port allocation mismatch"
mkdir -p "$BACKUP_ROOT" "$ROOT"
if [[ -f "$ROOT/index.html" ]]; then stamp="$(date +%Y%m%d-%H%M%S)"; tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-web-before-v$VERSION-$stamp.tgz" .; fi
rsync -a --delete --exclude='.git/' "$WEB_ROOT/" "$ROOT/"
cd "$ROOT"
docker compose -f compose.yml config --quiet
docker compose -f compose.yml build site-intelligence-web
docker compose -f compose.yml up -d --force-recreate site-intelligence-web
ready=0
for _ in $(seq 1 60); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
  [[ "$state" == healthy ]] && { ready=1; break; }
  [[ "$state" =~ ^(unhealthy|exited|dead)$ ]] && { docker logs --tail=120 "$CONTAINER" >&2 || true; fail "$CONTAINER entered $state"; }
  sleep 2
done
[[ "$ready" == 1 ]] || fail "$CONTAINER did not become healthy"
curl -fsS http://127.0.0.1:8096/healthz -o "$TMP/healthz.txt" || fail "web health request failed"
grep -q '^ok$' "$TMP/healthz.txt" || fail "web health check failed"
curl -fsS http://127.0.0.1:8096/config.js -o "$TMP/config.js" || fail "local config request failed"
grep -q '4.56.0' "$TMP/config.js" || fail "local release config failed"
grep -q 'standalone-production-certified' "$TMP/config.js" || fail "local runtime mode failed"

DEEP_LINKS=(country/KEN dossiers/KEN economics/KEN law/KEN science/KEN science/earth/KEN humanitarian/KEN resources/KEN events research packages/v4560-certification)
for path in "${DEEP_LINKS[@]}"; do
  safe="${path//\//_}"
  curl -fsS "http://127.0.0.1:8096/$path" -o "$TMP/$safe.html" || fail "deep link request failed: /$path"
  grep -q 'Connected Public Intelligence and Evidence Platform' "$TMP/$safe.html" || fail "deep link fallback failed: /$path"
done
echo "PASS: ${#DEEP_LINKS[@]} standalone deep-link aliases resolve through the production shell"

grep -q 'primaryService && !primaryService.ok' "$WEB_ROOT/app/assets/runtime-v3230.js" || fail "runtime health truth missing"
! grep -q 'failed >= 3' "$WEB_ROOT/app/assets/runtime-v3230.js" || fail "legacy false-offline threshold present"
curl -fsS http://127.0.0.1:8096/app/assets/runtime-v3230.js -o "$TMP/runtime.js" || fail "runtime asset request failed"
grep -q 'headers: { Accept: "application/json" }' "$TMP/runtime.js" || fail "simple-header runtime transport missing"
! grep -q '"X-SCSI-Runtime-Diagnostic": VERSION' "$TMP/runtime.js" || fail "runtime still forces diagnostic preflight header"
grep -q '4.56.0' "$WEB_ROOT/service-worker.js" || fail "root service-worker release identity mismatch"
grep -q '4.56.0' "$WEB_ROOT/app/service-worker.js" || fail "app service-worker release identity mismatch"

curl -fsS https://intelligence.sustainablecatalyst.com/config.js -o "$TMP/public-config.js" || fail "public HTTPS config request failed"
grep -q '4.56.0' "$TMP/public-config.js" || fail "public HTTPS release identity mismatch"
curl -fsS https://intelligence.sustainablecatalyst.com/economics/KEN -o "$TMP/public-economics.html" || fail "public HTTPS economics deep link failed"
grep -q 'Connected Public Intelligence and Evidence Platform' "$TMP/public-economics.html" || fail "public HTTPS shell mismatch"

echo "PASS: Site Intelligence v4.56.0 standalone web production consolidation & certification deployed on 127.0.0.1:8096"
