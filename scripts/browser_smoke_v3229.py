#!/usr/bin/env python3
"""Chromium visual smoke test for v3.23.5 vector cartography.

The test is network-independent. It supplies deterministic local raster tiles,
loads the packaged local country geometry, composes a satellite-like layer over
the basemap, and verifies visible geography, labels, controls, scale, overlay
order, non-zero dimensions, and a non-blank rendered screenshot.
"""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:  # Optional local visual-validation dependency.
    Image = None
    ImageDraw = None

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "backend/public_app/assets/vector-cartography-v3230.js"
CSS = ROOT / "backend/public_app/assets/vector-cartography-v3230.css"
WORLD = ROOT / "backend/public_app/assets/world-cartography-v3230.geojson"


def tile_png(kind: str) -> bytes:
    image = Image.new("RGBA", (256, 256), (10, 34, 46, 255) if kind == "base" else (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    if kind == "base":
        for y in range(0, 256, 32):
            draw.line((0, y, 256, y), fill=(42, 82, 94, 120), width=1)
        draw.rectangle((18, 24, 238, 232), outline=(86, 138, 151, 110), width=2)
    else:
        draw.ellipse((42, 38, 212, 208), fill=(91, 118, 101, 80), outline=(177, 205, 180, 90), width=3)
        draw.polygon(((15, 210), (120, 70), (246, 196)), fill=(112, 136, 97, 45))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def main() -> int:
    if Image is None or ImageDraw is None:
        print("SKIP: Pillow is unavailable.")
        return 0
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
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1360, "height": 900}, device_scale_factor=1)
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        base = tile_png("base")
        imagery = tile_png("imagery")
        page.route("https://tiles.example/base/**", lambda route: route.fulfill(status=200, body=base, content_type="image/png"))
        page.route("https://tiles.example/imagery/**", lambda route: route.fulfill(status=200, body=imagery, content_type="image/png"))
        page.set_content(
            '<!doctype html><html><body style="margin:0;background:#05090d">'
            '<div id="map" style="width:1080px;height:650px;margin:20px"></div>'
            '<div id="countryOverviewMap" style="width:1080px;height:500px;margin:20px"></div>'
            '</body></html>'
        )
        page.add_style_tag(content=CSS.read_text(encoding="utf-8"))
        page.evaluate("data => { window.fetch = async () => ({ok:true,json:async()=>data}); }", world)
        page.add_script_tag(content=ENGINE.read_text(encoding="utf-8"))
        result = page.evaluate(
            """async () => {
              const map=L.map('map').setView([5,25],2);
              const base=L.tileLayer('https://tiles.example/base/{z}/{x}/{y}.png',{maxZoom:8,role:'base'}).addTo(map);
              const imagery=L.tileLayer('https://tiles.example/imagery/{z}/{x}/{y}.png',{maxZoom:8,role:'imagery',opacity:.64,layerId:'true-color'}).addTo(map).bringToFront();
              L.circleMarker([0,0],{radius:9,color:'#fff',fillColor:'#e62b35'}).bindPopup('Test event').addTo(map);
              const layer=L.geoJSON({type:'Feature',properties:{name:'test'},geometry:{type:'Polygon',coordinates:[[[30,0],[40,0],[40,10],[30,10],[30,0]]]}},{style:{color:'#7cd8ff',fillColor:'#7cd8ff'}}).addTo(map);
              map.fitBounds(layer.getBounds());
              const second=L.map('countryOverviewMap').setView([0,0],2);
              L.tileLayer('https://invalid.example/{z}/{x}/{y}.png',{maxZoom:8,role:'base'}).addTo(second);
              await new Promise(resolve=>setTimeout(resolve,900));
              const summarize=id=>{const e=document.querySelector('#'+id);return {
                mode:e.dataset.scsiMapMode,status:e.dataset.scsiMapStatus,local:e.dataset.scsiLocalBasemap,
                boundaries:e.querySelectorAll('.scsi-local-basemap path').length,
                labels:e.querySelectorAll('.scsi-country-label').length,
                overlays:e.querySelectorAll('.scsi-map-overlay-root path,.scsi-map-overlay-root circle').length,
                controls:e.querySelectorAll('.scsi-map-controls button').length,
                baseTiles:e.querySelectorAll('.scsi-map-tile-layer--base img').length,
                imageryTiles:e.querySelectorAll('.scsi-map-tile-layer--imagery img').length,
                tileRoles:[...e.querySelectorAll('.scsi-map-tile-layer')].map(x=>x.dataset.tileRole),
                scale:e.querySelector('.scsi-map-scale')?.textContent.trim()||'',
                coordinates:e.querySelector('.scsi-map-coordinate-readout')?.textContent.trim()||'',
                width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height};};
              return {version:window.SCSIMapReliability.version,snapshot:window.SCSIMapReliability.snapshot(),first:summarize('map'),second:summarize('countryOverviewMap')};
            }"""
        )
        screenshot = page.locator("#map").screenshot(type="png")
        browser.close()

    image = Image.open(BytesIO(screenshot)).convert("RGB")
    colors = image.getcolors(maxcolors=image.width * image.height) or []
    dark_pixels = sum(count for count, rgb in colors if max(rgb) < 20)
    dark_ratio = dark_pixels / (image.width * image.height)
    unique_colors = len(colors)

    assert result["version"] == "3.23.5", result
    assert result["snapshot"]["libraryMode"] == "vector-cartography-engine", result
    assert result["snapshot"]["degradedCount"] == 0, result
    assert result["first"]["boundaries"] > 150, result
    assert result["second"]["boundaries"] > 150, result
    assert result["first"]["labels"] >= 5, result
    assert result["second"]["labels"] >= 10, result
    assert result["first"]["overlays"] >= 2, result
    assert result["first"]["controls"] == 3, result
    assert result["first"]["baseTiles"] > 0 and result["first"]["imageryTiles"] > 0, result
    assert result["first"]["tileRoles"][-1] == "imagery", result
    assert "km" in result["first"]["scale"], result
    assert "°" in result["first"]["coordinates"], result
    assert result["first"]["width"] > 0 and result["first"]["height"] > 0, result
    assert result["first"]["status"] == result["second"]["status"] == "ready", result
    assert unique_colors > 100, unique_colors
    assert dark_ratio < 0.72, dark_ratio
    assert not errors, errors
    print(json.dumps({**result, "visual": {"unique_colors": unique_colors, "dark_ratio": round(dark_ratio, 4)}}, indent=2))
    print("PASS: v3.23.5 rendered layered raster imagery, vector geography, country labels, overlays, scale, and controls in Chromium.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
