#!/usr/bin/env python3
"""Chromium smoke test for the self-hosted v3.22.8 map engine.

The test is intentionally network-independent. It injects the production engine,
its production CSS, and the bundled Natural Earth GeoJSON into Chromium, blocks
all tile delivery, and verifies that two map surfaces remain visible, interactive,
and healthy on the local vector basemap.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "backend/public_app/assets/map-engine-v3228.js"
CSS = ROOT / "backend/public_app/assets/map-engine-v3228.css"
WORLD = ROOT / "backend/public_app/assets/world-boundaries-v3228.geojson"


def main() -> int:
    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        print("SKIP: Chromium is unavailable.")
        return 0
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: Playwright is unavailable.")
        return 0

    world = json.loads(WORLD.read_text(encoding="utf-8"))
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=chromium,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        page.set_content('<!doctype html><html><body><div id="map" style="width:1000px;height:600px"></div><div id="countryOverviewMap" style="width:1000px;height:600px"></div></body></html>')
        page.add_style_tag(content=CSS.read_text(encoding="utf-8"))
        page.evaluate("data => { window.fetch = async () => ({ok:true,json:async()=>data}); }", world)
        page.add_script_tag(content=ENGINE.read_text(encoding="utf-8"))
        result = page.evaluate(
            """async () => {
              const map=L.map('map').setView([12,20],2);
              L.tileLayer('https://invalid.example/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
              L.circleMarker([0,0],{radius:8,color:'#fff',fillColor:'#f00'}).bindPopup('Test marker').addTo(map);
              const layer=L.geoJSON({type:'Feature',properties:{name:'test'},geometry:{type:'Polygon',coordinates:[[[30,0],[40,0],[40,10],[30,10],[30,0]]]}},{style:{color:'#0ff'}}).addTo(map);
              map.fitBounds(layer.getBounds());
              const second=L.map('countryOverviewMap').setView([0,0],2);
              await new Promise(resolve=>setTimeout(resolve,500));
              const summarize=id=>{const e=document.querySelector('#'+id);return {mode:e.dataset.scsiMapMode,status:e.dataset.scsiMapStatus,local:e.dataset.scsiLocalBasemap,boundaries:e.querySelectorAll('.scsi-local-basemap path').length,overlays:e.querySelectorAll('.scsi-map-overlay-root path,.scsi-map-overlay-root circle').length,controls:e.querySelectorAll('.scsi-map-controls button').length,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height};};
              return {version:window.SCSIMapReliability.version,snapshot:window.SCSIMapReliability.snapshot(),first:summarize('map'),second:summarize('countryOverviewMap')};
            }"""
        )
        browser.close()

    assert result["version"] == "3.22.8", result
    assert result["snapshot"]["libraryMode"] == "self-hosted-map-engine", result
    assert result["snapshot"]["degradedCount"] == 0, result
    assert result["first"]["boundaries"] > 150, result
    assert result["second"]["boundaries"] > 150, result
    assert result["first"]["overlays"] >= 2, result
    assert result["first"]["controls"] == 3, result
    assert result["first"]["width"] > 0 and result["first"]["height"] > 0, result
    assert result["first"]["status"] == result["second"]["status"] == "ready", result
    assert not errors, errors
    print(json.dumps(result, indent=2))
    print("PASS: v3.22.8 self-hosted map engine rendered local boundaries and overlays in Chromium.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
