#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.55.3.2.2"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-web-v4.55.3.2.2.zip}"
ROOT="${SC_WEB_ROOT:-/opt/sustainable-catalyst/site-intelligence-web}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
CONTAINER="${SC_WEB_CONTAINER:-sc-site-intelligence-web}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-web-v455322.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker curl; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "web package not found: $ARCHIVE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid web ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
WEB_ROOT="$(find "$TMP/package" -type f -name index.html -path '*/web/index.html' -print -quit | xargs -r dirname)"
[[ -n "$WEB_ROOT" && -f "$WEB_ROOT/config.js" && -f "$WEB_ROOT/compose.yml" ]] || fail "web package layout invalid"
grep -q 'release: "4.55.3.2.2"' "$WEB_ROOT/config.js" || fail "web release mismatch"
grep -q 'id="primaryNavigation"' "$WEB_ROOT/index.html" || fail "functional navigation missing"
grep -q 'id="economicsStudio"' "$WEB_ROOT/index.html" || fail "economics functional workspace missing"
grep -q 'id="scienceStudio"' "$WEB_ROOT/index.html" || fail "science functional workspace missing"
grep -q 'standalone-api-bridge-v45532.js' "$WEB_ROOT/index.html" || fail "standalone API bridge missing"
grep -q '/public/reliable/economics/records' "$WEB_ROOT/app/assets/standalone-api-bridge-v45532.js" || fail "reliable domain bridge missing"
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
curl -fsS http://127.0.0.1:8096/healthz -o "$TMP/healthz.txt" || fail "web health check request failed"
grep -q '^ok$' "$TMP/healthz.txt" || fail "web health check failed"

curl -fsS http://127.0.0.1:8096/economics/KEN -o "$TMP/economics.html" || fail "economics deep-link request failed"
grep -q 'Connected Public Intelligence and Evidence Platform' "$TMP/economics.html" || fail "economics deep-link functional app fallback failed"

curl -fsS http://127.0.0.1:8096/science/KEN -o "$TMP/science.html" || fail "science deep-link request failed"
grep -q 'standalone-api-bridge-v45532.js' "$TMP/science.html" || fail "science deep-link parity bridge failed"

curl -fsS http://127.0.0.1:8096/config.js -o "$TMP/config.js" || fail "web config request failed"
grep -q '4.55.3.2.2' "$TMP/config.js" || fail "web config release failed"

grep -q 'primaryService && !primaryService.ok' "$WEB_ROOT/app/assets/runtime-v3230.js" || fail "runtime health truth repair missing"
! grep -q 'failed >= 3' "$WEB_ROOT/app/assets/runtime-v3230.js" || fail "legacy false-offline threshold still present"
grep -q 'params.get("country") || qs("#countrySelect")?.value' "$WEB_ROOT/app/assets/economics-v220.js" || fail "economics country-context repair missing"
grep -q 'q.set("geography_code",resolved)' "$WEB_ROOT/app/assets/standalone-api-bridge-v45532.js" || fail "standalone deep-link geography propagation missing"
curl -fsS http://127.0.0.1:8096/app/assets/runtime-v3230.js -o "$TMP/runtime.js" || fail "runtime transport asset request failed"
grep -q 'headers: { Accept: "application/json" }' "$TMP/runtime.js" || fail "runtime transport did not remove custom-header requirement"
! grep -q '"X-SCSI-Runtime-Diagnostic": VERSION' "$TMP/runtime.js" || fail "runtime transport still forces diagnostic preflight header"
echo "PASS: Site Intelligence v4.55.3.2.2 standalone browser API transport repair deployed on 127.0.0.1:8096"
