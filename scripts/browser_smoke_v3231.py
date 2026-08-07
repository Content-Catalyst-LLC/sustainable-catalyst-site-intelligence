#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v3.27.0 production truth."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "backend/public_app/assets/production-truth-v3231.js"
STYLE = ROOT / "backend/public_app/assets/production-truth-v3231.css"


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

    routes = [
        {"route_id": "overview", "label": "Overview", "completion": "operational", "controller": None, "surface_selectors": ["#overviewLayout"], "endpoint_families": ["/public/geospatial/events"], "empty_state": "No matching records.", "degraded_state": "Overview is partially available.", "limitation": "Public evidence only.", "lazy_load": True},
        {"route_id": "global", "label": "Global conditions", "completion": "operational", "controller": "SCGlobalConditionsV210", "surface_selectors": ["#globalConditionsWorkspace"], "endpoint_families": ["/public/global-conditions"], "empty_state": "No current conditions.", "degraded_state": "Global conditions are partially available.", "limitation": "Coverage varies.", "lazy_load": True},
        {"route_id": "economics", "label": "Economics", "completion": "operational", "controller": "SCEconomicsV220", "surface_selectors": ["#economicsWorkspace"], "endpoint_families": ["/public/economics"], "empty_state": "No series.", "degraded_state": "Economics is partial.", "limitation": "Methods differ.", "lazy_load": True},
    ]
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"])
        page = browser.new_page(viewport={"width": 1200, "height": 820})
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        page.set_content('<!doctype html><html><body><nav id="primaryNavigation"><button class="nav-item active" data-route="overview"><span>Overview</span></button><button class="nav-item" data-route="global"><span>Global conditions</span></button><button class="nav-item" data-route="economics"><span>Economics</span></button></nav><main id="main" class="workspace"><header class="workspace-head"><h1 id="viewTitle">Overview</h1></header><section id="overviewLayout"><article class="panel"><p>Current public map, events, evidence, and source context are ready.</p><div class="scsi-map-managed"></div></article></section><section id="globalConditionsWorkspace" hidden><article class="panel"><p>Current global public conditions and source context are ready.</p></article></section><section id="routePanel" hidden></section></main></body></html>')
        page.evaluate("() => { window.__lastPushed=''; history.pushState=(state,title,url)=>{window.__lastPushed=String(url)}; }")
        page.add_style_tag(content=STYLE.read_text(encoding="utf-8"))
        page.evaluate("routes => { window.fetch=async()=>({ok:true,json:async()=>({ok:true,version:'3.27.0',routes})}); window.SCGlobalConditionsV210={open:async()=>{document.querySelector('#overviewLayout').hidden=true;document.querySelector('#globalConditionsWorkspace').hidden=false},close:()=>{document.querySelector('#globalConditionsWorkspace').hidden=true}}; let current='overview'; window.SCSIRouterV3228={current:()=>current,navigate:async route=>{current=route;document.querySelectorAll('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.route===route));if(route==='overview'){document.querySelector('#overviewLayout').hidden=false;window.SCGlobalConditionsV210.close()}else if(route==='global'){await window.SCGlobalConditionsV210.open()}return true}}; document.querySelector('#primaryNavigation').addEventListener('click',event=>{const button=event.target.closest('.nav-item[data-route]');if(button&&!button.disabled)window.SCSIRouterV3228.navigate(button.dataset.route)}); }", routes)
        page.add_script_tag(content=SCRIPT.read_text(encoding="utf-8"))
        page.wait_for_timeout(600)
        initial = page.evaluate("() => ({bar:!!document.querySelector('#productionTruthBar'),state:document.querySelector('#productionTruthBar')?.dataset.state,label:document.querySelector('#truthStateLabel')?.textContent,economicsDisabled:document.querySelector('[data-route=economics]').disabled,route:document.body.dataset.workspaceRoute})")
        page.click('[data-route="global"]')
        page.wait_for_timeout(450)
        global_state = page.evaluate("() => ({pushed:window.__lastPushed,state:document.querySelector('#productionTruthBar').dataset.state,route:document.body.dataset.workspaceRoute,globalVisible:!document.querySelector('#globalConditionsWorkspace').hidden})")
        browser.close()

    assert initial["bar"] and initial["state"] == "ready" and initial["route"] == "overview", initial
    assert initial["economicsDisabled"] is True, initial
    assert global_state["state"] == "ready" and global_state["route"] == "global" and global_state["globalVisible"] is True, global_state
    assert "view=global" in global_state["pushed"], global_state
    assert not errors, errors
    print(json.dumps({"initial": initial, "global": global_state}, indent=2))
    print("PASS: v3.27.0 production truth disabled a missing controller, reported route readiness, and restored browser history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
