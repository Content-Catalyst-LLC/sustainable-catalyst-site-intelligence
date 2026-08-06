#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v3.23.6 browser reliability."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "backend/public_app/assets/browser-reliability-v3235.js"
CSS = ROOT / "backend/public_app/assets/browser-reliability-v3235.css"


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
        "version": "3.23.6",
        "contract": "browser-reliability-mobile-accessibility",
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=chromium,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.on("console", lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
        page.set_content(
            '<!doctype html><html><body>'
            '<div id="routeAnnouncement" role="status"></div>'
            '<div id="app" data-scsi-release="3.23.6">'
            '<header class="topbar"><div class="topbar-controls"></div></header>'
            '<nav id="primaryNavigation"><button class="nav-item" data-route="overview" aria-current="page">Overview</button></nav>'
            '<main><section data-route-panel><h1>Live intelligence workspace</h1>'
            '<div id="map" class="map" role="img" aria-label="Public event map"><svg><path d="M0 0L10 10"/></svg><i data-event-id="e1"></i></div>'
            '</section></main>'
            '<button id="openDrawer" aria-controls="evidenceDrawer">Open evidence</button>'
            '<aside id="evidenceDrawer" aria-hidden="false"><button id="drawerFirst">First</button><button id="closeEvidenceDrawer">Close</button></aside>'
            '</div></body></html>'
        )
        page.add_style_tag(content=CSS.read_text(encoding="utf-8"))
        page.evaluate("payload=>{window.fetch=async()=>({ok:true,json:async()=>payload});}", contract)
        page.add_script_tag(content=JS.read_text(encoding="utf-8"))
        page.wait_for_timeout(250)
        result = page.evaluate(
            """() => ({
              ready: Boolean(window.SCSIBrowserReliabilityV3235),
              viewport: document.documentElement.dataset.scsiViewport,
              summary: document.querySelector('#map-summary')?.textContent || '',
              touchTarget: getComputedStyle(document.documentElement).getPropertyValue('--scsi-touch-target').trim(),
              status: Boolean(document.querySelector('#scsiReliabilityStatus')),
              low: document.documentElement.dataset.scsiLowBandwidth
            })"""
        )
        page.click("#scsiLowBandwidthToggle")
        low_after = page.evaluate("document.documentElement.dataset.scsiLowBandwidth")
        page.keyboard.press("Alt+m")
        page.evaluate("window.SCSIBrowserReliabilityV3235.focusRoute('overview')")
        focused = page.evaluate("document.activeElement?.textContent")
        browser.close()

    assert result["ready"] is True, result
    assert result["viewport"] == "phone", result
    assert "Public event map" in result["summary"] and "1 event markers" in result["summary"], result
    assert result["touchTarget"] == "44px", result
    assert result["status"] is True, result
    assert low_after == "true", low_after
    assert focused == "Live intelligence workspace", focused
    assert not errors, errors
    print(json.dumps({**result, "low_after": low_after, "focused": focused}, indent=2))
    print("PASS: v3.23.6 mobile viewport, map summary, low-bandwidth mode, and route focus rendered without browser errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
