#!/usr/bin/env python3
"""Verify the global country picker keeps focus and remains fully selectable.

Native ``<select>`` popups are owned by the host operating system. Headless Chrome
on macOS does not consistently apply Home/End to a closed native popup, so this
release gate verifies the portable contract instead: a complete unique catalog,
focus retention, unblocked wheel events, and successful selection at both ends of
the catalog plus a representative middle-country selection.
"""
from __future__ import annotations

import json
import os
import traceback

from browser_complete_shell_gate_v32362 import document, find_browser


def wait_for_badge(page, value: str) -> None:
    page.wait_for_function(
        "expected => (document.querySelector('#dataTruthBadge')?.textContent || '').trim() === expected",
        arg=value,
        timeout=5000,
    )


def exercise(page, label: str) -> dict[str, object]:
    page.wait_for_function(
        "document.querySelectorAll('#countrySelect option').length >= 170",
        timeout=20000,
    )
    page.wait_for_timeout(1200)

    catalog = page.evaluate(
        """()=>{
          const select=document.querySelector('#countrySelect');
          const values=[...select.options].map(option=>option.value).filter(Boolean);
          const style=getComputedStyle(select);
          const wheel=new WheelEvent('wheel',{deltaY:160,bubbles:true,cancelable:true});
          const dispatchResult=select.dispatchEvent(wheel);
          return {
            count: values.length,
            uniqueCount: new Set(values).size,
            firstOption: values[0] || '',
            lastOption: values.at(-1) || '',
            hasKenya: values.includes('KEN'),
            hasBrazil: values.includes('BRA'),
            disabled: select.disabled,
            pointerEvents: style.pointerEvents,
            visibility: style.visibility,
            wheelDefaultPrevented: wheel.defaultPrevented,
            wheelDispatchResult: dispatchResult,
          };
        }"""
    )

    page.focus("#countrySelect")
    immediate = page.evaluate("document.activeElement?.id || ''")
    page.evaluate(
        """()=>{
          const main=document.querySelector('#main');
          for(let i=0;i<12;i++){
            window.dispatchEvent(new CustomEvent('scsi:workspace-state',{detail:{version:'4.15.0',route:'overview',state:i%2?'ready':'degraded'}}));
            const probe=document.createElement('i');probe.className='selector-focus-probe';main?.append(probe);probe.remove();
          }
        }"""
    )
    page.wait_for_timeout(750)
    retained = page.evaluate("document.activeElement?.id || ''")

    first_option = str(catalog["firstOption"])
    last_option = str(catalog["lastOption"])
    page.locator("#countrySelect").select_option(last_option)
    wait_for_badge(page, last_option)
    selected_last = page.locator("#countrySelect").input_value()

    page.locator("#countrySelect").select_option(first_option)
    wait_for_badge(page, first_option)
    selected_first = page.locator("#countrySelect").input_value()

    page.locator("#countrySelect").select_option("BRA")
    wait_for_badge(page, "BRA")
    selected = page.locator("#countrySelect").input_value()
    badge = (page.locator("#dataTruthBadge").text_content() or "").strip()

    return {
        "label": label,
        **catalog,
        "immediateFocus": immediate,
        "retainedFocus": retained,
        "selectedLast": selected_last,
        "selectedFirst": selected_first,
        "selected": selected,
        "badge": badge,
        "activeAfterSelection": page.evaluate("document.activeElement?.id || ''"),
    }


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for the selector interaction gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for the selector interaction gate.")
        return 2

    errors: list[str] = []
    results: list[dict[str, object]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        html, _ = document("disabled")
        direct = browser.new_page(viewport={"width": 1280, "height": 900})
        direct.on("pageerror", lambda error: errors.append(f"direct:{error}"))
        direct.set_content(html, wait_until="domcontentloaded", timeout=45000)
        results.append(exercise(direct, "direct"))
        direct.close()

        outer = browser.new_page(viewport={"width": 1280, "height": 920})
        outer.set_content('<iframe id="gate" style="width:1180px;height:820px;border:0"></iframe>')
        frame = outer.query_selector("#gate").content_frame()
        assert frame is not None
        frame.set_content(html, wait_until="domcontentloaded", timeout=45000)
        results.append(exercise(frame, "iframe"))
        outer.close()
        browser.close()

    assert not errors, errors
    for result in results:
        assert result["count"] >= 170, result
        assert result["uniqueCount"] == result["count"], result
        assert result["firstOption"] and result["lastOption"], result
        assert result["firstOption"] != result["lastOption"], result
        assert result["hasKenya"] is True and result["hasBrazil"] is True, result
        assert result["disabled"] is False, result
        assert result["pointerEvents"] != "none" and result["visibility"] == "visible", result
        assert result["wheelDefaultPrevented"] is False and result["wheelDispatchResult"] is True, result
        assert result["immediateFocus"] == "countrySelect", result
        assert result["retainedFocus"] == "countrySelect", result
        assert result["selectedLast"] == result["lastOption"], result
        assert result["selectedFirst"] == result["firstOption"], result
        assert result["selected"] == "BRA" and result["badge"] == "BRA", result
    print(json.dumps({"browser": browser_path, "results": results, "errors": errors}, indent=2))
    print("PASS: v4.15.0 preserves country-picker focus, leaves wheel interaction unblocked, and selects the first, last, and representative catalog countries in direct and iframe modes.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        import sys
        sys.stdout.flush(); sys.stderr.flush()
    finally:
        os._exit(status)
