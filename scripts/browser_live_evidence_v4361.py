#!/usr/bin/env python3
"""Deterministic browser certification for v4.36.1 Ocean/Space live-evidence bindings.

The browser runs the shipped workspace modules against the real first-party FastAPI
catalog/state contracts through TestClient. External NOAA, OBIS and NASA calls are
intercepted with bounded fixtures so release certification is deterministic and does
not make upstream availability a deployment prerequisite.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "backend" / "public_app" / "assets"

sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import find_browser

sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from app.main import app

VERSION = "4.36.1"

FIXTURES = {
    "/public/authoritative-connectors/noaa-erddap/search": {
        "ok": True,
        "version": VERSION,
        "connector_id": "noaa-coastwatch-erddap",
        "source": "NOAA CoastWatch ERDDAP",
        "query": "Sea-surface temperature",
        "result_count": 2,
        "datasets": [
            {
                "Dataset ID": "fixtureSST",
                "Title": "Fixture SST",
                "Summary": "Bounded NOAA SST discovery fixture",
                "griddap": "https://coastwatch.noaa.gov/erddap/griddap/fixtureSST",
            },
            {
                "Dataset ID": "fixtureSST2",
                "Title": "Fixture SST 2",
                "Summary": "Second bounded NOAA SST discovery fixture",
                "tabledap": "https://coastwatch.noaa.gov/erddap/tabledap/fixtureSST2",
            },
        ],
        "retrieved_at": "2026-08-16T00:00:00Z",
        "boundary": "Fixture data validates browser binding only.",
    },
    "/public/authoritative-connectors/obis/occurrences": {
        "ok": True,
        "version": VERSION,
        "connector_id": "obis-api-v3",
        "source": "IOC-UNESCO Ocean Biodiversity Information System",
        "record_count": 1,
        "upstream_total": 1,
        "records": [
            {
                "scientificName": "Delphinus delphis",
                "eventDate": "2026-01-01",
                "decimalLatitude": 1.0,
                "decimalLongitude": 2.0,
                "basisOfRecord": "HumanObservation",
                "datasetName": "Fixture OBIS dataset",
            }
        ],
        "retrieved_at": "2026-08-16T00:00:00Z",
        "boundary": "Fixture data validates browser binding only.",
    },
    "/public/authoritative-connectors/noaa-coops/data": {
        "ok": True,
        "version": VERSION,
        "connector_id": "noaa-coops-data-api",
        "source": "NOAA CO-OPS Data API",
        "query": {
            "product": "water_level",
            "station": "9414290",
            "units": "metric",
            "time_zone": "gmt",
            "datum": "MSL",
            "date": "latest",
        },
        "metadata": {
            "id": "9414290",
            "name": "San Francisco",
            "lat": "37.8063",
            "lon": "-122.4659",
        },
        "record_count": 1,
        "records": [{"t": "2026-08-16 00:00", "v": "0.52", "f": "0,0,0,0", "q": "v"}],
        "retrieved_at": "2026-08-16T00:00:00Z",
        "boundary": "Fixture data validates browser binding only.",
    },
    "/public/exoplanet-habitability/live": {
        "ok": True,
        "version": VERSION,
        "connector_id": "nasa-exoplanet-tap",
        "source": "NASA Exoplanet Archive TAP",
        "record_count": 1,
        "records": [
            {
                "planet_name": "TRAPPIST-1 e",
                "host_name": "TRAPPIST-1",
                "discovery_method": "Transit",
                "discovery_year": 2017,
                "orbital_period_days": 6.1,
                "planet_radius_earth": 0.92,
                "planet_mass_earth": 0.69,
                "equilibrium_temperature_k": 250,
                "system_distance_pc": 12.4,
            }
        ],
        "retrieved_at": "2026-08-16T00:00:00Z",
        "boundary": "Fixture data validates browser binding only.",
    },
    "/public/authoritative-connectors/nasa-cmr/collections": {
        "ok": True,
        "version": VERSION,
        "connector_id": "nasa-cmr-search",
        "source": "NASA EOSDIS Common Metadata Repository",
        "mode": "DISCOVERY",
        "collection_count": 1,
        "collections": [
            {
                "title": "Fixture Mars Collection",
                "short_name": "MARS_FIXTURE",
                "version_id": "1",
                "granule_count": 3,
                "summary": "Bounded CMR metadata fixture",
            }
        ],
        "retrieved_at": "2026-08-16T00:00:00Z",
        "boundary": "Fixture data validates browser binding only.",
    },
}

HTML_TEMPLATE = """<!doctype html><html><head><meta charset='utf-8'></head><body>
<section id='earthStudio'><div class='earth-studio-actions'></div>
  <section id='earthOrbitPanel'></section>
  <section id='planetaryPanel' hidden></section>
</section>
<section id='oceanSurfacePanel' hidden></section>
<section id='marineBiodiversityPanel' hidden></section>
<section id='marinePollutionPanel'><div class='mp41300-actions'></div></section>
<section id='astronomyPanel'></section>
<section id='exoplanetHabitabilityPanel' hidden></section>
<script>
window.SC_SITE_INTELLIGENCE_API='https://gate.local';
try { history.replaceState = () => {}; history.pushState = () => {}; } catch (_) {}
window.open = () => null;
const __payloads=__PAYLOADS__;
const __planetaryStates=__PLANETARY_STATES__;
window.__connectorRequests=[];
window.fetch=async(input)=>{
  const u=new URL(String(input),'https://gate.local');
  const path=u.pathname;
  if(path.startsWith('/public/authoritative-connectors/') || path==='/public/exoplanet-habitability/live') window.__connectorRequests.push(path);
  let payload=__payloads[path];
  if(path==='/public/planetary-intelligence/state') payload=__planetaryStates[u.searchParams.get('body')==='mars'?'mars':'moon'];
  if(!payload) return new Response(JSON.stringify({detail:'deterministic browser fixture unavailable: '+path}),{status:503,headers:{'Content-Type':'application/json'}});
  return new Response(JSON.stringify(payload),{status:200,headers:{'Content-Type':'application/json'}});
};
</script>
</body></html>"""

MODULES = [
    "ocean-surface-v4500.js",
    "marine-biodiversity-v4900.js",
    "coastal-change-v41400.js",
    "exoplanet-habitability-v43500.js",
    "planetary-intelligence-v4200.js",
]


def get_json(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def browser_payloads(client: TestClient):
    moon = get_json(client, "/public/planetary-intelligence/body/moon")
    mars = get_json(client, "/public/planetary-intelligence/body/mars")
    moon_product = moon["body"]["products"][0]["id"]
    mars_product = mars["body"]["products"][0]["id"]
    payloads = {
        "/public/ocean-intelligence/catalog": get_json(client, "/public/ocean-intelligence/catalog"),
        "/public/ocean-intelligence/state": get_json(client, "/public/ocean-intelligence/state?variable=sea-surface-temperature&source=noaa-coastwatch-erddap&latitude=0&longitude=0&date="),
        "/public/marine-biodiversity/catalog": get_json(client, "/public/marine-biodiversity/catalog"),
        "/public/marine-biodiversity/state": get_json(client, "/public/marine-biodiversity/state?source=obis&evidence_class=occurrence-record&scientific_name=Delphinus%20delphis&date="),
        "/public/coastal-change/catalog": get_json(client, "/public/coastal-change/catalog"),
        "/public/coastal-change/state": get_json(client, "/public/coastal-change/state?source=noaa-coops&indicator_type=observed-water-level&date="),
        "/public/exoplanet-habitability/catalog": get_json(client, "/public/exoplanet-habitability/catalog"),
        "/public/exoplanet-habitability/state": get_json(client, "/public/exoplanet-habitability/state?source=nasa-exoplanet-archive-systems&indicator_type=planetary-system&target=TRAPPIST-1%20e&facility=JWST&wavelength_um=4.3"),
        "/public/planetary-intelligence/body/moon": moon,
        "/public/planetary-intelligence/body/mars": mars,
        **FIXTURES,
    }
    planetary_states = {
        "moon": get_json(client, f"/public/planetary-intelligence/state?body=moon&product={moon_product}"),
        "mars": get_json(client, f"/public/planetary-intelligence/state?body=mars&product={mars_product}"),
    }
    return payloads, planetary_states


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for the v4.36.1 browser gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for the v4.36.1 browser gate.")
        return 2

    client = TestClient(app)
    payloads, planetary_states = browser_payloads(client)
    html = HTML_TEMPLATE.replace("__PAYLOADS__", json.dumps(payloads, separators=(",", ":"))).replace("__PLANETARY_STATES__", json.dumps(planetary_states, separators=(",", ":")))
    errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(html, wait_until="domcontentloaded", timeout=30000)

        for name in MODULES:
            page.add_script_tag(content=(ASSETS / name).read_text(encoding="utf-8"))

        page.evaluate("async()=>{await window.SCSIOceanSurfaceV4500.enter(); return true}")
        page.wait_for_function("document.querySelector('#oceanLiveBadge')?.textContent.includes('live dataset')", timeout=12000)
        ocean = page.evaluate("()=>({badge:document.querySelector('#oceanLiveBadge')?.textContent||'',cards:document.querySelectorAll('#oceanLiveEvidence article').length})")
        assert ocean["cards"] >= 2, ocean

        page.evaluate("async()=>{await window.SCSIMarineBiodiversityV4900.enter(); return true}")
        page.wait_for_function("document.querySelector('#bioLiveBadge')?.textContent.includes('shown')", timeout=12000)
        biodiversity = page.evaluate("()=>({badge:document.querySelector('#bioLiveBadge')?.textContent||'',cards:document.querySelectorAll('#bioLiveRecords article').length})")
        assert biodiversity["cards"] >= 1, biodiversity

        page.evaluate("async()=>{await window.SCSICoastalChangeV41400.enter(); return true}")
        page.wait_for_function("document.querySelector('#ccLiveBadge')?.textContent.includes('record')", timeout=12000)
        coastal = page.evaluate("()=>({badge:document.querySelector('#ccLiveBadge')?.textContent||'',cards:document.querySelectorAll('#ccLiveRecords article').length})")
        assert coastal["cards"] >= 1, coastal

        page.evaluate("async()=>{await window.SCSIExoplanetHabitabilityV43500.enter(); return true}")
        page.wait_for_function("document.querySelector('#exoLiveBadge')?.textContent.includes('live record')", timeout=12000)
        exoplanet = page.evaluate("()=>({badge:document.querySelector('#exoLiveBadge')?.textContent||'',cards:document.querySelectorAll('#exoLiveRecords article').length})")
        assert exoplanet["cards"] >= 1, exoplanet

        page.evaluate("async()=>{await window.SCSIPlanetaryV4200.enter(); const b=document.querySelector('#planetaryBody'); b.value='mars'; b.dispatchEvent(new Event('change')); return true}")
        page.wait_for_function("document.querySelector('#planetaryCmrBadge')?.textContent.includes('discovery record')", timeout=12000)
        page.wait_for_function("document.querySelector('#planetaryBodyTitle')?.textContent==='Mars'", timeout=12000)
        planetary = page.evaluate("()=>({badge:document.querySelector('#planetaryCmrBadge')?.textContent||'',cards:document.querySelectorAll('#planetaryCmrRecords article').length,title:document.querySelector('#planetaryBodyTitle')?.textContent||''})")
        assert planetary["cards"] >= 1 and planetary["title"] == "Mars", planetary

        connector_requests = page.evaluate("()=>Array.from(new Set(window.__connectorRequests||[])).sort()")
        browser.close()

    assert not errors, errors
    required_requests = sorted(FIXTURES)
    assert set(required_requests).issubset(set(connector_requests)), sorted(set(required_requests) - set(connector_requests))
    result = {
        "ocean": ocean,
        "biodiversity": biodiversity,
        "coastal": coastal,
        "exoplanet": exoplanet,
        "planetary": planetary,
        "connector_requests": connector_requests,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    print("PASS: v4.36.1 browser modules render bounded NOAA, OBIS and NASA connector records.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(status)
