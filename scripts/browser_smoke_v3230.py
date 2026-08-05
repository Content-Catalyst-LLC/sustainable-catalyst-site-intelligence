#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v3.23.1 application presentation."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "backend/public_app/assets/vector-cartography-v3230.js"
ENGINE_CSS = ROOT / "backend/public_app/assets/vector-cartography-v3230.css"
WORKSPACE = ROOT / "backend/public_app/assets/cartographic-workspace-v3230.js"
WORKSPACE_CSS = ROOT / "backend/public_app/assets/cartographic-workspace-v3230.css"
WORLD = ROOT / "backend/public_app/assets/world-cartography-v3230.geojson"


def tile_png() -> bytes:
    image = Image.new("RGBA", (256, 256), (10, 34, 46, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(0, 256, 32):
        draw.line((0, y, 256, y), fill=(42, 82, 94, 130), width=1)
    draw.rectangle((14, 18, 242, 238), outline=(86, 138, 151, 130), width=2)
    output = BytesIO(); image.save(output, format="PNG"); return output.getvalue()


def main() -> int:
    if Image is None or ImageDraw is None:
        print("SKIP: Pillow is unavailable."); return 0
    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        print("SKIP: Chromium is unavailable."); return 0
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: Playwright is unavailable."); return 0

    world = json.loads(WORLD.read_text(encoding="utf-8"))
    countries = {"ok": True, "countries": [{"code": "KEN", "name": "Kenya", "latitude": 0.0236, "longitude": 37.9062, "default_zoom": 5}]}
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        tile = tile_png()
        page.route("https://tiles.example/**", lambda route: route.fulfill(status=200, body=tile, content_type="image/png"))
        page.set_content('''<!doctype html><html><body><div class="app-shell"><header class="topbar"></header><aside class="sidebar"><nav id="primaryNavigation"><button class="nav-item active" data-route="overview"><span>Overview</span><small>Live map</small></button><button class="nav-item" data-route="spatial"><span>Spatial</span><small>Evidence</small></button></nav></aside><main id="main" class="workspace"><section class="workspace-head"><div><h1>Climate and Human Vulnerability</h1><p>Public evidence</p></div></section><section class="map-panel"><div class="map-toolbar"><select id="countrySelect"><option value="KEN">Kenya</option></select><div class="map-actions"></div></div><div id="map"></div><div class="map-legend"></div></section><section class="metric-grid"><article class="metric-card"><strong>148</strong></article><article class="metric-card"><strong>Kenya</strong></article></section><section class="content-grid"><article class="panel"><div class="panel-head"><h2>Recent events</h2></div></article><article class="panel"><div class="panel-head"><h2>Country context</h2></div></article></section><section id="routePanel" hidden></section></main></div></body></html>''')
        page.add_style_tag(content=ENGINE_CSS.read_text(encoding="utf-8"))
        page.add_style_tag(content=WORKSPACE_CSS.read_text(encoding="utf-8"))
        page.evaluate("([world,countries]) => { window.fetch=async url=>({ok:true,json:async()=>String(url).includes('/public/countries')?countries:world}); }", [world, countries])
        page.add_script_tag(content=ENGINE.read_text(encoding="utf-8"))
        page.evaluate("""() => { const map=L.map('map',{minZoom:2,maxZoom:9}).setView([0,20],2); L.tileLayer('https://tiles.example/{z}/{x}/{y}.png',{role:'base',maxZoom:9}).addTo(map); L.circleMarker([0.02,37.9],{radius:8}).addTo(map); }""")
        page.add_script_tag(content=WORKSPACE.read_text(encoding="utf-8"))
        page.wait_for_timeout(1100)
        first = page.evaluate("""() => { const map=document.querySelector('#map'), layout=document.querySelector('#overviewLayout'), rail=document.querySelector('#overviewEvidenceRail'), strip=document.querySelector('#mapPresentationStatus'); return {overviewLayout:!!layout,rail:!!rail,railOpen:rail?.classList.contains('is-open'),metricsInRail:!!rail?.querySelector('.metric-grid'),width:map.getBoundingClientRect().width,height:map.getBoundingClientRect().height,paths:map.querySelectorAll('.scsi-local-basemap path').length,tiles:map.querySelectorAll('.scsi-map-tile-layer img').length,controls:map.querySelectorAll('.scsi-map-controls button').length,presentationHealth:map.dataset.scsiPresentationHealth,status:strip?.dataset.state,bodyRoute:document.body.dataset.activeRoute,center:window.SCSIMapReliability.getMap('map').getCenter(),zoom:window.SCSIMapReliability.getMap('map').getZoom()}; }""")
        page.evaluate("""() => { document.querySelectorAll('.nav-item').forEach(item=>item.classList.toggle('active',item.dataset.route==='spatial')); window.SCSICartographicWorkspaceV3230.syncRoute(); }""")
        page.wait_for_timeout(120)
        route_hidden = page.evaluate("() => document.querySelector('#overviewLayout').hidden && getComputedStyle(document.querySelector('#overviewLayout')).display==='none'")
        page.evaluate("""() => { document.querySelectorAll('.nav-item').forEach(item=>item.classList.toggle('active',item.dataset.route==='overview')); window.SCSICartographicWorkspaceV3230.syncRoute(); window.SCSICartographicWorkspaceV3230.setRailOpen(false); }""")
        page.wait_for_timeout(120)
        closed = page.evaluate("() => document.querySelector('#overviewEvidenceRail').classList.contains('is-collapsed')")
        screenshot = page.locator("#main").screenshot(type="png")
        browser.close()

    image = Image.open(BytesIO(screenshot)).convert("RGB")
    colors = image.getcolors(maxcolors=image.width * image.height) or []
    dark_ratio = sum(count for count, rgb in colors if max(rgb) < 20) / (image.width * image.height)
    result = {**first, "routeHidden": route_hidden, "drawerClosed": closed, "uniqueColors": len(colors), "darkRatio": round(dark_ratio, 4)}
    assert result["overviewLayout"] and result["rail"] and result["metricsInRail"], result
    assert result["width"] >= 700 and result["height"] >= 500, result
    assert result["paths"] >= 170 and result["tiles"] > 0 and result["controls"] >= 2, result
    assert result["presentationHealth"] == "ready" and result["status"] == "ready", result
    assert result["bodyRoute"] == "overview" and result["routeHidden"] and result["drawerClosed"], result
    assert abs(result["center"]["lat"] - 0.0236) < 1 and abs(result["center"]["lng"] - 37.9062) < 2, result
    assert result["zoom"] >= 4, result
    assert result["uniqueColors"] > 100 and result["darkRatio"] < 0.82, result
    assert not errors, errors
    print(json.dumps(result, indent=2))
    print("PASS: v3.23.1 rendered a bounded map-first workspace, subject focus, evidence drawer, route isolation, and visible-map health in Chromium.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
