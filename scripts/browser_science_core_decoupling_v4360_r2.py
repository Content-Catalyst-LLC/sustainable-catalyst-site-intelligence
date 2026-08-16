#!/usr/bin/env python3
"""Browser certification for v4.37.0 R2 Science Core-decoupling.

Reproduces the reported production condition: Platform Core is unconfigured.
The Science domain selector must still expose and launch Ocean and Space.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import document, find_browser
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from app.main import app


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for the v4.37.0 R2 Science browser gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for the v4.37.0 R2 Science browser gate.")
        return 2

    client = TestClient(app)
    overview = client.get("/public/scientific-earth-systems").json()
    assert overview["integration"]["state"] == "core-unconfigured", overview["integration"]
    html, _ = document("disabled")
    errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))

        def fulfill_public(route):
            parsed = urlsplit(route.request.url)
            if not parsed.path.startswith("/public/"):
                route.continue_()
                return
            target = parsed.path + ("?" + parsed.query if parsed.query else "")
            response = client.get(target)
            body = response.content
            route.fulfill(status=response.status_code, content_type=response.headers.get("content-type", "application/json"), body=body)

        page.route("**/public/**", fulfill_public)
        page.set_content(html, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
        page.wait_for_function("document.documentElement.dataset.v4Navigation === 'ready'", timeout=12000)

        page.evaluate("async()=>{await window.SCSIRouterV3228.navigate('science'); return true}")
        page.wait_for_function("!document.querySelector('#scienceStudio')?.hidden", timeout=10000)
        page.wait_for_selector('#scienceWorkspaceSelect', state="visible", timeout=10000)
        page.wait_for_function("document.querySelectorAll('#scienceWorkspaceSelect option').length === 3", timeout=10000)

        initial = page.evaluate("""()=>({
          status:document.querySelector('#scienceStatus span:last-child')?.textContent||'',
          coreNotice:document.querySelector('#scienceCoreRecordNotice')?.innerText||'',
          options:[...document.querySelectorAll('#scienceWorkspaceSelect option')].map(x=>x.textContent),
          coreFamilyDisabled:document.querySelector('#scienceFamily')?.disabled||false,
          localCardCount:document.querySelectorAll('#scienceWorkspaceCards .science-workspace-card').length
        })""")
        assert initial["options"] == ["Earth", "Ocean", "Space"], initial
        assert initial["coreFamilyDisabled"] is True, initial
        assert "Earth, Ocean, and Space" in initial["status"] and "available" in initial["status"], initial
        assert "optional" in initial["coreNotice"].lower(), initial

        page.select_option('#scienceWorkspaceSelect', 'ocean')
        page.wait_for_selector('[data-science-local-action="ocean"]', state="visible", timeout=5000)
        page.locator('[data-science-local-action="ocean"]').click()
        page.wait_for_function("!document.querySelector('#oceanObservationStudio')?.hidden", timeout=12000)
        ocean = page.evaluate("""()=>({
          visible:!document.querySelector('#oceanObservationStudio')?.hidden,
          cards:document.querySelectorAll('[data-ocean-card]').length,
          title:document.querySelector('#viewTitle')?.textContent||''
        })""")
        assert ocean["visible"] is True and ocean["cards"] == 11, ocean

        await_science = """async()=>{await window.SCSIRouterV3228.navigate('science'); await window.SCScienceV240.open(); return true}"""
        page.evaluate(await_science)
        page.wait_for_function("!document.querySelector('#scienceStudio')?.hidden", timeout=10000)
        page.select_option('#scienceWorkspaceSelect', 'space')
        page.wait_for_selector('[data-science-local-action="planetary"]', state="visible", timeout=5000)
        space = page.evaluate("""()=>({
          cardCount:document.querySelectorAll('#scienceWorkspaceCards .science-workspace-card').length,
          actions:[...document.querySelectorAll('#scienceWorkspaceCards [data-science-local-action]')].map(x=>x.dataset.scienceLocalAction),
          titles:[...document.querySelectorAll('#scienceWorkspaceCards h4')].map(x=>x.textContent)
        })""")
        assert space["cardCount"] >= 6, space
        assert {"orbital-earth", "planetary", "astronomy", "solar-system", "exoplanets", "seti"}.issubset(set(space["actions"])), space
        assert client.get("/public/planetary-intelligence/body/moon").json()["product_count"] >= 1

        browser.close()

    assert not errors, errors
    print(json.dumps({"browser": browser_path, "initial": initial, "ocean": ocean, "space": space, "errors": errors}, indent=2))
    print("PASS: v4.37.0 R2 Science remains usable with Platform Core unconfigured and launches both Ocean and Space.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        sys.stdout.flush(); sys.stderr.flush()
    finally:
        os._exit(status)
