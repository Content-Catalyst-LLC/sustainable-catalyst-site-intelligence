#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.55.3"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-web-v4.55.3.zip}"
ROOT="${SC_WEB_ROOT:-/opt/sustainable-catalyst/site-intelligence-web}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
CONTAINER="${SC_WEB_CONTAINER:-sc-site-intelligence-web}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-web-v4553.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker curl; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "web package not found: $ARCHIVE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid web ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
WEB_ROOT="$(find "$TMP/package" -type f -name index.html -path '*/web/index.html' -print -quit | xargs -r dirname)"
[[ -n "$WEB_ROOT" && -f "$WEB_ROOT/config.js" && -f "$WEB_ROOT/compose.yml" ]] || fail "web package layout invalid"
grep -q 'release: "4.55.3"' "$WEB_ROOT/config.js" || fail "web release mismatch"
grep -q 'https://site-intelligence-api.sustainablecatalyst.com' "$WEB_ROOT/config.js" || fail "API origin mismatch"
grep -q 'try_files \$uri \$uri/ /index.html' "$WEB_ROOT/nginx.conf" || fail "SPA history fallback missing"
mkdir -p "$BACKUP_ROOT" "$ROOT"
if [[ -f "$ROOT/index.html" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-web-before-v$VERSION-$stamp.tgz" .
fi
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
curl -fsS http://127.0.0.1:8092/healthz | grep -q '^ok$' || fail "web health check failed"
curl -fsS http://127.0.0.1:8092/economics/KEN | grep -q 'Standalone application' || fail "deep-link SPA fallback failed"
curl -fsS http://127.0.0.1:8092/config.js | grep -q '4.55.3' || fail "web config release failed"
echo "PASS: Site Intelligence v4.55.3 standalone web application deployed locally on 127.0.0.1:8092"
echo "NEXT: expose intelligence.sustainablecatalyst.com through Caddy using deploy/contabo/site-intelligence-web-v4553.Caddyfile"
