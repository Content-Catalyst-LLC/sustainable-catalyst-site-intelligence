#!/usr/bin/env python3
"""Verify the shipped shell hydrates and operates the global country selector."""
from __future__ import annotations

import json
import traceback

from browser_complete_shell_gate_v32362 import document, find_browser


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for the country-selector gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for the country-selector gate.")
        return 2

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        html, _ = document("disabled")
        page.set_content(html, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_function(
            "document.querySelectorAll('#countrySelect option').length >= 170",
            timeout=20000,
        )
        initial = page.evaluate(
            """()=>({count:document.querySelectorAll('#countrySelect option').length,
            value:document.querySelector('#countrySelect').value,
            hasBrazil:Boolean(document.querySelector('#countrySelect option[value="BRA"]'))})"""
        )
        page.select_option("#countrySelect", "BRA")
        page.wait_for_function("document.querySelector('#countrySelect').value === 'BRA'", timeout=5000)
        page.click("#dataTruthToggle")
        page.wait_for_selector("text=Brazil (BRA)", timeout=12000)
        result = {
            "browser": browser_path,
            "initial": initial,
            "selected": page.locator("#countrySelect").input_value(),
            "truthHeading": page.locator("text=Brazil (BRA)").first.text_content(),
            "badge": page.locator("#dataTruthBadge").text_content(),
            "api": page.evaluate("window.SCSIDataTruthV32371.version"),
            "errors": errors,
        }
        browser.close()

    assert not errors, errors
    assert initial["count"] >= 170 and initial["value"] == "KEN" and initial["hasBrazil"]
    assert result["selected"] == "BRA" and result["badge"] == "BRA"
    assert result["api"] == "4.13.0"
    print(json.dumps(result, indent=2))
    print("PASS: v4.13.0 hydrates the global selector and changes Data Truth from Kenya to Brazil.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    raise SystemExit(status)
