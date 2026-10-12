#!/usr/bin/env bash
set -euo pipefail
WEB="${SCSI_WEB_ORIGIN:-https://intelligence.sustainablecatalyst.com}"
API="${SCSI_API_ORIGIN:-https://site-intelligence-api.sustainablecatalyst.com}"
failures=0
check(){
  local label="$1" url="$2" type="${3:-asset}" output status
  output="$(mktemp)"
  status="$(curl --max-time 40 -sSL -o "$output" -w '%{http_code}' "$url" || true)"
  if [[ "$status" != "200" || ! -s "$output" ]]; then
    echo "FAIL $label http=$status"; failures=$((failures+1)); rm -f "$output"; return
  fi
  if [[ "$type" == "json" ]]; then
    if ! python3 -m json.tool "$output" >/dev/null 2>&1; then
      echo "FAIL $label invalid-json"; failures=$((failures+1)); rm -f "$output"; return
    fi
  fi
  echo "PASS $label http=$status bytes=$(wc -c < "$output" | tr -d ' ')"
  rm -f "$output"
}
echo "Site Intelligence v4.57.0 static and API parity preflight"
check "frontend" "$WEB/"
check "map engine" "$WEB/app/assets/vector-cartography-v3230.js"
check "boundaries" "$WEB/app/assets/world-cartography-v3230.geojson" json
check "app router" "$WEB/app/assets/app.js"
check "NASA/orbital module" "$WEB/app/assets/orbital-earth-v4100.js"
check "ocean hub" "$WEB/app/assets/ocean-observation-v4360.js"
check "planetary module" "$WEB/app/assets/planetary-intelligence-v4200.js"
check "API health" "$API/health" json
check "countries" "$API/public/countries" json
check "economics records KEN" "$API/public/economics-sustainability/records?geography_code=KEN&limit=10" json
check "ocean catalog" "$API/public/ocean-observation" json
check "country KEN" "$API/public/country/KEN" json
echo "HTTP/JSON failures: $failures"
echo "NOTE: This preflight does not verify record counts, source coverage, imagery tiles, or browser rendering."
echo "NOTE: Follow with interactive checks for country/earth/ocean routes, images, map layers, and provenance."
test "$failures" -eq 0
