#!/usr/bin/env python3
"""Deterministic browser smoke for the v4.38.0 first-class Ocean workspace."""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import document, find_browser
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from app.main import app


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for v4.38.0 Ocean browser gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for v4.38.0 Ocean browser gate.")
        return 2

    client = TestClient(app)
    catalog = client.get("/public/ocean-observation/catalog").json()
    readiness = client.get("/public/ocean-observation/readiness").json()
    html, _ = document("disabled")
    errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1360, "height": 940})
        page.on("pageerror", lambda error: errors.append(str(error)))

        def fulfill(route):
            url = route.request.url
            if "/public/ocean-observation/readiness" in url:
                payload = readiness
            elif "/public/ocean-observation/catalog" in url:
                payload = catalog
            else:
                route.continue_()
                return
            route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

        page.route("**/public/ocean-observation/**", fulfill)
        page.set_content(html, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
        page.wait_for_function("document.documentElement.dataset.v4Navigation === 'ready'", timeout=12000)
        page.wait_for_selector('#primaryNavigation > .v4000-nav-featured [data-ocean-entry="hub"]', state="attached", timeout=12000)
        page.locator('#primaryNavigation > .v4000-nav-featured [data-ocean-entry="hub"]').click(timeout=12000)
        page.wait_for_function("!document.querySelector('#oceanObservationStudio')?.hidden", timeout=10000)
        page.wait_for_selector('[data-ocean-card="surface"]', timeout=10000)
        result = page.evaluate(
            """()=>({
              visible:!document.querySelector('#oceanObservationStudio')?.hidden,
              oceanActive:document.querySelector('#primaryNavigation [data-ocean-entry="hub"]')?.classList.contains('active')||false,
              earthActive:document.querySelector('#primaryNavigation .nav-item[data-route="earth"]')?.classList.contains('active')||false,
              cardCount:document.querySelectorAll('[data-ocean-card]').length,
              groupCount:document.querySelectorAll('.ocean4360-group').length,
              dataTruth:(document.querySelector('.ocean4360-truth')?.innerText||'').includes('DATA TRUTH'),
              title:(document.querySelector('#viewTitle')?.textContent||'').trim(),
              url:location.search,
              oceanFeatured:Boolean(document.querySelector('#primaryNavigation > .v4000-nav-featured [data-ocean-entry="hub"]'))
            })"""
        )
        browser.close()

    assert not errors, errors
    assert result["oceanFeatured"] is True, result
    assert result["visible"] is True, result
    assert result["oceanActive"] is True and result["earthActive"] is False, result
    assert result["cardCount"] == 11, result
    assert result["groupCount"] == 5, result
    assert result["dataTruth"] is True, result
    assert "Ocean observation" in result["title"], result
    assert catalog["system_count"] == 11 and readiness["ok"] is True
    print(json.dumps({"browser": browser_path, "result": result, "errors": errors}, indent=2))
    print("PASS: v4.38.0 R1 Ocean workspace survives v4 navigation regrouping and is first-class, visible, grouped and source-bound.")
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
