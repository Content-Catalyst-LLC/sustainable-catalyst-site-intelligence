#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.55.3.1.1"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-web-v4.55.3.1.1.zip}"
ROOT="${SC_WEB_ROOT:-/opt/sustainable-catalyst/site-intelligence-web}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
CONTAINER="${SC_WEB_CONTAINER:-sc-site-intelligence-web}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-web-v455311.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker curl; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "web package not found: $ARCHIVE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid web ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
WEB_ROOT="$(find "$TMP/package" -type f -name index.html -path '*/web/index.html' -print -quit | xargs -r dirname)"
[[ -n "$WEB_ROOT" && -f "$WEB_ROOT/config.js" && -f "$WEB_ROOT/compose.yml" ]] || fail "web package layout invalid"
grep -q 'release: "4.55.3.1.1"' "$WEB_ROOT/config.js" || fail "web release mismatch"
grep -q '/public/reliable/economics/records' "$WEB_ROOT/assets/views.js" || fail "reliable API surface not wired into standalone views"
grep -q 'probe:true' "$WEB_ROOT/assets/views.js" || fail "live capability probe not wired into standalone home"
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
curl -fsS http://127.0.0.1:8096/healthz | grep -q '^ok$' || fail "web health check failed"
curl -fsS http://127.0.0.1:8096/science/KEN | grep -q 'Standalone application' || fail "science deep-link SPA fallback failed"
curl -fsS http://127.0.0.1:8096/config.js | grep -q '4.55.3.1.1' || fail "web config release failed"
echo "PASS: Site Intelligence v4.55.3.1.1 standalone web deployed on 127.0.0.1:8096"
