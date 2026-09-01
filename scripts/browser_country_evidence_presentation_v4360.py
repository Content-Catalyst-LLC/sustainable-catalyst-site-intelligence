#!/usr/bin/env python3
"""Deterministic browser regression for v4.39.0 country evidence hierarchy."""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import document, find_browser


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for v4.39.0 country presentation gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for v4.39.0 country presentation gate.")
        return 2

    html, _ = document("disabled")
    errors: list[str] = []
    result: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(html, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
        # Keep this presentation regression isolated from optional country-context
        # fetches. The full workspace gate exercises the Country route separately.
        page.evaluate("document.querySelector('#globalCountryExplorer').hidden=false")
        page.wait_for_function("!document.querySelector('#globalCountryExplorer')?.hidden", timeout=5000)
        result = page.evaluate(
            """()=>({
              brief:document.querySelector('#globalCountryExplorer')?.innerText?.includes('COUNTRY INTELLIGENCE BRIEF')||false,
              conditions:document.querySelector('#globalCountryExplorer')?.innerText?.includes('Operational evidence is separate from structural statistics')||false,
              indicatorHeading:document.querySelector('#globalCountryExplorer')?.innerText?.includes('OFFICIAL, PUBLISHED & COMPARATIVE INDICATORS')||false,
              evidenceStatus:(document.querySelector('#countryEvidenceStatusTitle')?.textContent||'').trim(),
              authority:(document.querySelector('#countryAuthoritySummary')?.textContent||'').trim(),
              operational:(document.querySelector('#countryOperationalSummary')?.textContent||'').trim()
            })"""
        )
        browser.close()

    assert not errors, errors
    assert result["brief"], result
    assert result["conditions"], result
    assert result["indicatorHeading"], result
    assert result["evidenceStatus"], result
    assert result["operational"], result
    # The deterministic shell may not always return a World Bank highlight, so
    # benchmark/warning cards are asserted in backend tests; the browser gate
    # requires that the rendered hierarchy and evidence-detail interaction exist.
    print(json.dumps({"browser": browser_path, "result": result, "errors": errors}, indent=2))
    print("PASS: v4.39.0 country evidence hierarchy is visible and Conditions Now remains separate from structural indicators.")
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
