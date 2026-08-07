#!/usr/bin/env python3
"""Mandatory browser gate for Site Intelligence v3.28.0 cross-view state."""
from __future__ import annotations

import json
import os
import traceback

from browser_complete_shell_gate_v32362 import document, find_browser


def exercise(page, label: str) -> dict[str, object]:
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
    page.wait_for_function("window.SiteIntelligenceCrossViewState && document.documentElement.dataset.crossViewState === 'ready'", timeout=12000)
    page.wait_for_function("document.querySelectorAll('#countrySelect option').length >= 170", timeout=20000)
    page.locator('#countrySelect').select_option('BRA')
    page.wait_for_timeout(250)
    page.click('[data-cross-view-target="compare"]')
    page.wait_for_function("window.SCSIRouterV3228?.current?.() === 'compare'", timeout=12000)
    page.wait_for_timeout(250)
    compare = page.evaluate("""()=>({
      state:window.SiteIntelligenceCrossViewState.current(),
      url:location.search,
      route:window.SCSIRouterV3228.current(),
      country:document.querySelector('#countrySelect')?.value,
      barCountry:document.querySelector('#crossViewCountry')?.textContent,
      fingerprint:document.querySelector('#crossViewFingerprint')?.textContent,
      actions:document.querySelectorAll('[data-cross-view-target]').length,
      canonical:window.SiteIntelligenceCrossViewState.canonical('compare')
    })""")
    page.click('[data-cross-view-target="earth"]')
    page.wait_for_function("window.SCSIRouterV3228?.current?.() === 'earth'", timeout=12000)
    page.wait_for_timeout(250)
    earth = page.evaluate("""()=>({
      state:window.SiteIntelligenceCrossViewState.current(),
      url:location.search,
      route:window.SCSIRouterV3228.current(),
      country:document.querySelector('#countrySelect')?.value,
      canonical:window.SiteIntelligenceCrossViewState.canonical('country')
    })""")
    return {'label': label, 'compare': compare, 'earth': earth}


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for the cross-view state gate.')
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for the cross-view state gate.')
        return 2

    results: list[dict[str, object]] = []
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=browser_path, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu-sandbox'])
        html, _ = document('disabled')
        direct = browser.new_page(viewport={'width': 1360, 'height': 940})
        direct.on('pageerror', lambda error: errors.append(f'direct:{error}'))
        direct.set_content(html, wait_until='domcontentloaded', timeout=45000)
        results.append(exercise(direct, 'direct'))
        direct.close()

        outer = browser.new_page(viewport={'width': 1360, 'height': 960})
        outer.set_content('<iframe id="gate" style="width:1240px;height:880px;border:0"></iframe>')
        frame = outer.query_selector('#gate').content_frame()
        assert frame is not None
        frame.set_content(html, wait_until='domcontentloaded', timeout=45000)
        results.append(exercise(frame, 'iframe'))
        outer.close()
        browser.close()

    assert not errors, errors
    for result in results:
        compare = result['compare']; earth = result['earth']
        assert compare['route'] == 'compare' and compare['country'] == 'BRA', result
        assert compare['state']['country'] == 'BRA' and compare['state']['view'] == 'compare', result
        assert 'view=compare' in compare['canonical'] and 'country=BRA' in compare['canonical'], result
        assert compare['barCountry'] == 'BRA' and len(compare['fingerprint']) == 8, result
        assert compare['actions'] == 5, result
        assert earth['route'] == 'earth' and earth['country'] == 'BRA', result
        assert earth['state']['country'] == 'BRA' and earth['state']['view'] == 'earth', result
        assert earth['state']['view'] == 'earth' and earth['state']['country'] == 'BRA', result
        assert 'view=country' in earth['canonical'] and 'country=BRA' in earth['canonical'], result
    print(json.dumps({'browser': browser_path, 'results': results, 'errors': errors}, indent=2))
    print('PASS: v3.28.0 preserved country and analytical state across compare, Earth observation, direct, iframe, and portable deep-link transitions.')
    return 0


if __name__ == '__main__':
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
