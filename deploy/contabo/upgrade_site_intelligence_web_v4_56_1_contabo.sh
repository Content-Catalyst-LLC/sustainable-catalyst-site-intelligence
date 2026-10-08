#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="4.56.1"
ARCHIVE="${1:-/tmp/sustainable-catalyst-site-intelligence-web-v4.56.1.zip}"
ROOT="${SC_WEB_ROOT:-/opt/sustainable-catalyst/site-intelligence-web}"
BACKUP_ROOT="${SC_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
TMP="$(mktemp -d /tmp/sc-site-intelligence-web-v4561.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail(){ echo "ERROR: $*" >&2; exit 1; }
for cmd in unzip rsync docker curl tar grep; do command -v "$cmd" >/dev/null || fail "$cmd is required"; done
[[ -f "$ARCHIVE" ]] || fail "web package not found: $ARCHIVE"
unzip -tq "$ARCHIVE" >/dev/null || fail "invalid web ZIP"
unzip -q "$ARCHIVE" -d "$TMP/package"
config="$(find "$TMP/package" -type f -path '*/web/config.js' | head -1)"
[[ -n "$config" ]] || fail "web/config.js missing"
SRC_WEB="$(dirname "$config")"
grep -Fq 'release: "4.56.1"' "$config" || fail "web package release mismatch"
mkdir -p "$ROOT" "$BACKUP_ROOT"
stamp="$(date +%Y%m%d-%H%M%S)"
if [[ -d "$ROOT/app" ]]; then tar -C "$ROOT" -czf "$BACKUP_ROOT/site-intelligence-web-before-v$VERSION-$stamp.tgz" .; fi
rsync -a --delete --exclude='.git/' "$SRC_WEB/" "$ROOT/"
cd "$ROOT"
docker compose config --quiet
docker compose build site-intelligence-web
docker compose up -d --force-recreate site-intelligence-web
ready=0
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8096/healthz >/dev/null 2>&1; then ready=1; break; fi
  sleep 2
done
[[ "$ready" == 1 ]] || fail "standalone web did not become healthy"
curl -fsS http://127.0.0.1:8096/config.js -o "$TMP/config.js"
grep -Fq 'release: "4.56.1"' "$TMP/config.js" || fail "local web release mismatch"
grep -Fq 'runtimeMode: "standalone-production-certified-core-bridge"' "$TMP/config.js" || fail "runtime mode mismatch"
for path in / /country/KEN /dossiers/KEN /economics/KEN /law/KEN /science/KEN /humanitarian/KEN /resources/KEN /events /research; do
  curl -fsS "http://127.0.0.1:8096$path" -o "$TMP/page.html" || fail "deep link failed: $path"
  grep -Fq 'Connected Public Intelligence and Evidence Platform' "$TMP/page.html" || fail "shell identity missing: $path"
done
echo "PASS: Site Intelligence v4.56.1 standalone web deployed on 127.0.0.1:8096"
