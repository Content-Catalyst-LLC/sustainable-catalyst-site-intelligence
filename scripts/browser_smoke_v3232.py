#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v4.1.0 map interaction controls."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "backend/public_app/assets/vector-cartography-v3230.js"
ENGINE_CSS = ROOT / "backend/public_app/assets/vector-cartography-v3230.css"
INTERACTION = ROOT / "backend/public_app/assets/cartographic-interaction-v3232.js"
INTERACTION_CSS = ROOT / "backend/public_app/assets/cartographic-interaction-v3232.css"
WORLD = ROOT / "backend/public_app/assets/world-cartography-v3230.geojson"


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
    features = [
        {"type":"Feature","id":"eq-1","geometry":{"type":"Point","coordinates":[37.9,0.02]},"properties":{"id":"eq-1","title":"Kenya earthquake","category":"earthquake","source":"USGS","magnitude":5.6,"observed_at":"2026-08-04T12:00:00Z"}},
        {"type":"Feature","id":"fire-1","geometry":{"type":"Point","coordinates":[39.1,-1.2]},"properties":{"id":"fire-1","title":"Thermal anomaly","category":"wildfire","source":"NASA EONET","observed_at":"2026-08-03T12:00:00Z"}},
        {"type":"Feature","id":"flood-1","geometry":{"type":"Point","coordinates":[36.8,-0.5]},"properties":{"id":"flood-1","title":"Flood record","category":"flood","source":"ReliefWeb","observed_at":"2026-08-02T12:00:00Z"}},
    ]
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        page.set_content('<!doctype html><html><body><div id="app" data-scsi-release="4.1.0" class="app-ready"><section class="map-panel"><div class="map-toolbar"><div class="map-actions"></div></div><div id="map" style="width:1000px;height:560px"></div><div id="eventList"></div></section></div></body></html>')
        page.add_style_tag(content=ENGINE_CSS.read_text(encoding="utf-8"))
        page.add_style_tag(content=INTERACTION_CSS.read_text(encoding="utf-8"))
        page.evaluate("world => { window.fetch=async()=>({ok:true,json:async()=>world}); }", world)
        page.add_script_tag(content=ENGINE.read_text(encoding="utf-8"))
        page.evaluate("features => { history.replaceState=()=>{}; const map=L.map('map',{minZoom:2,maxZoom:9}).setView([0,38],3); let filters={categories:[],source:'',days:30,cluster:true,eventsVisible:true,selected:''}; let filtered=features.slice(); const redraw=()=>{filtered=features.filter(f=>(!filters.categories.length||filters.categories.includes(f.properties.category))&&(!filters.source||filters.source===f.properties.source)); window.dispatchEvent(new CustomEvent('scsi:overview-events-rendered',{detail:{count:filtered.length}}));}; window.SCSIOverviewMapV3232={version:'4.1.0',getMap:()=>map,getEvents:()=>features,getFilteredEvents:()=>filtered,getFilters:()=>({...filters}),setFilters:next=>{filters={...filters,...next};redraw();return filters},selectEvent:id=>{filters.selected=id},fitResults:()=>map.fitBounds(filtered.map(f=>[f.geometry.coordinates[1],f.geometry.coordinates[0]]),{maxZoom:6}),setImageryOpacity:value=>{document.querySelector('#map').dataset.opacity=String(value)},setBaseStyle:value=>{document.querySelector('#map').dataset.mapStyle=value},syncUrl:()=>{},render:redraw}; redraw(); }", features)
        page.add_script_tag(content=INTERACTION.read_text(encoding="utf-8"))
        page.wait_for_timeout(800)
        page.click('#mapInteractionToggle')
        page.select_option('#mapCategoryFilter','earthquake')
        page.fill('#mapImageryOpacity','40')
        page.dispatch_event('#mapImageryOpacity','input')
        page.select_option('#mapBaseStyle','evidence-neutral')
        page.click('#mapFitResults')
        result = page.evaluate("() => ({panelVisible:!document.querySelector('#mapInteractionPanel').hidden,category:document.querySelector('#mapCategoryFilter').value,sourceOptions:document.querySelector('#mapSourceFilter').options.length,legend:document.querySelectorAll('#mapSemanticLegend span').length,summary:document.querySelector('#mapFilterSummary')?.textContent,style:document.querySelector('#map').dataset.mapStyle,opacity:document.querySelector('#map').dataset.opacity,paths:document.querySelectorAll('#map .scsi-local-basemap path').length,controls:document.querySelectorAll('#map .scsi-map-controls button').length,center:window.SCSIOverviewMapV3232.getMap().getCenter(),zoom:window.SCSIOverviewMapV3232.getMap().getZoom()})")
        browser.close()
    assert result["panelVisible"] and result["category"] == "earthquake", result
    assert result["sourceOptions"] == 4 and result["legend"] == 7, result
    assert "1 mapped records" in result["summary"], result
    assert result["style"] == "evidence-neutral" and result["opacity"] == "0.4", result
    assert result["paths"] >= 170 and result["controls"] >= 2, result
    assert result["zoom"] >= 4, result
    assert not errors, errors
    print(json.dumps(result, indent=2))
    print("PASS: v4.1.0 rendered layer controls, semantic filters, synchronized result state, fit-to-results, and local geography in Chromium.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
