# Site Intelligence v4.61.0 — Ocean Salinity & Water Properties

## Scope
Adds a source-bounded NOAA CoastWatch SMOS near-real-time daily sea-surface salinity adapter, read-only public route, standalone interactive salinity geographic map and provenance-preserving JSON export. Existing SST and chlorophyll paths unchanged.

## Scientific dataset contract
- Source: NOAA NESDIS CoastWatch, `coastwatchSMOSv662SSS1day` (SMOS MIRAS Level 3).
- Variable: `sss`, practical salinity, PSU. 4 axes: time, altitude (0 m), ascending latitude (-89.875..89.875), ascending longitude (-179.875..179.875). Daily centered time 12:00 UTC.
- Source metadata: https://coastwatch.pfeg.noaa.gov/erddap/griddap/coastwatchSMOSv662SSS1day.html
- Query: bounded 1-degree, 0.25-degree grid, <=256KiB and 2500 points; fail closed on wrong day, wrong altitude, unexpected units, invalid values, oversized responses. SHA256 upstream raw-byte receipt, no independent scientific accuracy certification.
- `GET /public/ocean-intelligence/noaa/salinity/grid?latitude=12&longitude=-65&date=2026-10-01`.
- Registry source `noaa-smos-daily-salinity` remains `integration-pending` until actual live retrieval and browser verification.

## On Contabo — pull and run tests
```bash
cd /opt/sustainable-catalyst/site-intelligence-v4563
git pull --ff-only origin main
PYTHONPATH=. /tmp/scsi-v4575-test/bin/python -m pytest -q \
 tests/test_salinity_v4610.py tests/test_chlorophyll_v4600.py \
 tests/test_ocean_contracts_v4590.py tests/test_ocean_consolidation_v4580.py \
 tests/test_noaa_grid_v4577.py tests/test_noaa_erddap_v4576.py \
 tests/test_ocean_surface_visualization_v4575.py -o addopts=""
```
Stop on any test failures.

## Backend deployment (preserve custom main.py)
```bash
cd /opt/sustainable-catalyst
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$HOME/scsi-v4610-$STAMP"
cp site-intelligence/backend/app/main.py "$HOME/scsi-v4610-$STAMP/main.py"
cp site-intelligence/backend/app/ocean_contracts_v4590.py "$HOME/scsi-v4610-$STAMP/ocean_contracts_v4590.py"
cp site-intelligence-v4563/backend/app/salinity_v4610.py site-intelligence/backend/app/salinity_v4610.py
cp site-intelligence-v4563/backend/app/ocean_contracts_v4590.py site-intelligence/backend/app/ocean_contracts_v4590.py
cd site-intelligence
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py");s=p.read_text()
anchor="from .chlorophyll_v4600 import retrieve_chlorophyll_grid"
block='''from .salinity_v4610 import retrieve_salinity_grid

@app.get("/public/ocean-intelligence/noaa/salinity/grid")
def public_noaa_salinity_grid(latitude: float = Query(..., ge=-85, le=85), longitude: float = Query(..., ge=-175, le=175), date: str = Query(...)):
    return retrieve_salinity_grid(latitude, longitude, date)

'''
if 'def public_noaa_salinity_grid(' in s:print("Already present")
elif s.count(anchor)!=1:raise SystemExit("Unique anchor missing")
else:p.write_text(s.replace(anchor,block+anchor,1));print("Route installed")
PY
python3 -m py_compile backend/app/main.py backend/app/salinity_v4610.py backend/app/ocean_contracts_v4590.py
docker compose up -d --build site-intelligence
docker compose ps
```
Wait for backend health. Test live query:
```bash
curl -sS -G 'https://site-intelligence-api.sustainablecatalyst.com/public/ocean-intelligence/noaa/salinity/grid' --data-urlencode latitude=12 --data-urlencode longitude=-65 --data-urlencode date=2026-10-01 | python3 -m json.tool
```
If `unavailable`, capture message before frontend deployment and verify NOAA source request/metadata, avoiding claims of successful retrieval.

## Frontend after backend PASS
```bash
cd /opt/sustainable-catalyst
STAMP=$(date +%Y%m%d-%H%M%S)
cp site-intelligence-web/index.html "$HOME/scsi-v4610-web-$STAMP-index.html"
cp site-intelligence-v4563/web/index.html site-intelligence-web/index.html
cp site-intelligence-v4563/web/app/assets/ocean-salinity-v4610.js site-intelligence-web/app/assets/ocean-salinity-v4610.js
cd site-intelligence-web
docker compose up -d --build site-intelligence-web
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' https://intelligence.sustainablecatalyst.com/app/assets/ocean-salinity-v4610.js
```
Navigate Ocean Surface. The Salinity panel has its own controls and provides map plus receipt-bearing JSON export. Verify SST and chlorophyll unaffected. No migrations, no new credential, no production writes.
