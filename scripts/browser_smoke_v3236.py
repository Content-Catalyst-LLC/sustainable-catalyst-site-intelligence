#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v4.6.0 performance/offline recovery."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "backend/public_app/assets/performance-offline-v3236.js"
CSS = ROOT / "backend/public_app/assets/performance-offline-v3236.css"
WORKER = ROOT / "backend/public_app/service-worker.js"


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

    errors: list[str] = []
    contract = {
        "ok": True,
        "version": "4.6.0",
        "contract": "performance-and-offline-recovery",
        "performance_budgets": {"first_useful_map_ms": 3500},
    }
    html = f'''<!doctype html><html><head><style>{CSS.read_text(encoding="utf-8")}</style></head><body>
      <div id="app" data-scsi-release="4.6.0">
        <nav id="primaryNavigation"><button class="nav-item" data-route="overview" aria-current="page">Overview</button><button class="nav-item" data-route="science">Science</button></nav>
        <main><section data-route-panel data-route="overview"><h1>Overview</h1><div id="map" style="width:900px;height:520px" aria-label="Public intelligence map"></div></section><section data-route-panel data-route="science" hidden><h1>Science</h1></section></main>
      </div>
      <script>window.fetch=async()=>new Response(JSON.stringify({json.dumps(contract)}),{{status:200,headers:{{'Content-Type':'application/json'}}}})</script>
      <script>{JS.read_text(encoding="utf-8")}</script>
      <script>setTimeout(()=>document.querySelector('#map').innerHTML='<svg><path d="M0 0 L100 100"></path></svg>',35)</script>
    </body></html>'''

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.on("console", lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))

        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_function("window.SCSIPerformanceOfflineV3236 && window.SCSIPerformanceOfflineV3236.getState().firstUsefulMapMs !== null")
        result = page.evaluate("""() => { const s=window.SCSIPerformanceOfflineV3236.getState(); return {ready:Boolean(window.SCSIPerformanceOfflineV3236),route:s.route,firstUsefulMapMs:s.firstUsefulMapMs,status:document.querySelector('#scsiPerformanceStatus')?.dataset.state,text:document.querySelector('.scsi-performance-copy')?.textContent,offline:document.documentElement.dataset.scsiOffline,requests:s.requests,inflight:s.inflight}; }""")
        page.evaluate("""() => { const a=document.querySelector('[data-route="overview"]'); const b=document.querySelector('[data-route="science"]'); a.removeAttribute('aria-current'); b.setAttribute('aria-current','page'); document.querySelector('section[data-route="overview"]').hidden=true; document.querySelector('section[data-route="science"]').hidden=false; window.dispatchEvent(new CustomEvent('scsi:workspace-state',{detail:{route:'science',state:'ready'}})); }""")
        page.wait_for_timeout(80)
        route_result = page.evaluate("""() => ({route:window.SCSIPerformanceOfflineV3236.getState().route, overview:document.querySelector('section[data-route="overview"]').dataset.scsiRouteActive, science:document.querySelector('section[data-route="science"]').dataset.scsiRouteActive})""")
        browser.close()

    assert result["ready"] is True, result
    assert result["route"] == "overview", result
    assert isinstance(result["firstUsefulMapMs"], int) and result["firstUsefulMapMs"] < 3500, result
    assert result["status"] == "ready", result
    assert "Map ready" in result["text"], result
    assert route_result == {"route": "science", "overview": "false", "science": "true"}, route_result
    assert not errors, errors
    print(json.dumps({"initial": result, "route": route_result}, indent=2))
    print("PASS: v4.6.0 first-useful-map measurement, route isolation, and recovery status rendered without browser errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
