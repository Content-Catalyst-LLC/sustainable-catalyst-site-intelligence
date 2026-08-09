#!/usr/bin/env python3
"""Mandatory browser gate for Site Intelligence v4.11.0 Global Data Truth Control Plane."""
from __future__ import annotations

import json
import os
import traceback

from browser_complete_shell_gate_v32362 import document, find_browser


def exercise(page, label: str) -> dict[str, object]:
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
    page.wait_for_function("window.SCSIDataTruthV32371 && window.SCSIDataTruthControlPlaneV3240", timeout=12000)
    page.click('#dataTruthToggle')
    page.click('[data-truth-view="control"]')
    page.wait_for_selector('.scsi-control-table tbody tr', state='visible', timeout=10000)
    page.wait_for_function("document.querySelectorAll('.scsi-control-workspaces article').length >= 10", timeout=10000)
    before = page.evaluate("""()=>({
      active:document.querySelector('[data-truth-view="control"]')?.getAttribute('aria-selected'),
      sources:document.querySelectorAll('.scsi-control-table tbody tr').length,
      workspaces:document.querySelectorAll('.scsi-control-workspaces article').length,
      incidents:document.querySelectorAll('.scsi-control-incident-list article').length,
      drift:document.querySelectorAll('.scsi-control-drift-list article').length,
      summary:document.querySelectorAll('.scsi-control-summary article').length,
      fingerprint:(document.querySelector('.scsi-control-boundaries code')?.textContent||'').trim(),
      country:document.querySelector('#countrySelect')?.value||'',
      api:Boolean(window.SCSIDataTruthControlPlaneV3240?.renderInto)
    })""")
    page.fill('#dataTruthControlFilter', 'World Bank')
    page.wait_for_timeout(100)
    filtered = page.evaluate("""()=>({
      visible:[...document.querySelectorAll('[data-control-source]')].filter(row=>!row.hidden).length,
      hidden:[...document.querySelectorAll('[data-control-source]')].filter(row=>row.hidden).length
    })""")
    page.fill('#dataTruthControlFilter', '')
    return {'label': label, 'before': before, 'filtered': filtered}


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for the data-truth control-plane gate.')
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for the data-truth control-plane gate.')
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
        before = result['before']
        filtered = result['filtered']
        assert before['active'] == 'true', result
        assert before['sources'] == 8, result
        assert before['workspaces'] == 12, result
        assert before['drift'] == 8, result
        assert before['summary'] == 7, result
        assert len(before['fingerprint']) == 64, result
        assert before['country'] == 'KEN' and before['api'] is True, result
        assert filtered['visible'] == 1 and filtered['hidden'] == 7, result
    print(json.dumps({'browser': browser_path, 'results': results, 'errors': errors}, indent=2))
    print('PASS: v4.11.0 rendered the Global Data Truth Control Plane with source operations, schema drift, incidents, workspace truth, filtering, and fingerprint disclosure in direct and iframe modes.')
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
