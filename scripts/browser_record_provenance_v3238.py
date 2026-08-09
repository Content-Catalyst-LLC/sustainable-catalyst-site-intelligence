#!/usr/bin/env python3
"""Mandatory browser gate for v4.11.0 record provenance and indicator truth."""
from __future__ import annotations

import json
import os
import traceback

from browser_complete_shell_gate_v32362 import document, find_browser


def exercise(page, label: str) -> dict[str, object]:
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
    page.wait_for_function("window.SCSIRecordProvenanceV3238 && window.SCSIDataTruthV32371", timeout=12000)

    page.click('#mapLayerTruthButton')
    page.wait_for_function("!document.querySelector('#recordTruthPanel')?.hidden && window.SCSIRecordProvenanceV3238?.getCurrent?.()?.record_type === 'map_layer'", timeout=8000)
    layer = page.evaluate("window.SCSIRecordProvenanceV3238.getCurrent()")
    page.click('#recordTruthClose')

    page.click('#dataTruthToggle')
    page.wait_for_selector('[data-record-truth-indicator]', state='visible', timeout=8000)
    page.click('[data-record-truth-indicator="SP.POP.TOTL"]')
    page.wait_for_function("window.SCSIRecordProvenanceV3238?.getCurrent?.()?.record_id === 'indicator:KEN:SP.POP.TOTL'", timeout=8000)
    indicator = page.evaluate("window.SCSIRecordProvenanceV3238.getCurrent()")

    page.evaluate("window.SCSIRecordProvenanceV3238.openRecord({record_type:'event',id:'browser-gate-event',title:'Browser gate event',source:'USGS',source_url:'https://earthquake.usgs.gov/',observed_at:'2026-08-05T00:00:00Z',country_code:'USA',data_state:'live'})")
    page.wait_for_function("window.SCSIRecordProvenanceV3238?.getCurrent?.()?.record_id === 'event:browser-gate-event'", timeout=8000)
    event = page.evaluate("window.SCSIRecordProvenanceV3238.getCurrent()")

    return {
        'label': label,
        'layer': {
            'id': layer.get('record_id'),
            'type': layer.get('record_type'),
            'state': layer.get('truth_state'),
            'fingerprint': len((layer.get('fingerprint') or {}).get('value') or ''),
        },
        'indicator': {
            'id': indicator.get('record_id'),
            'type': indicator.get('record_type'),
            'state': indicator.get('truth_state'),
            'year': (indicator.get('dates') or {}).get('observation_year'),
            'fingerprint': len((indicator.get('fingerprint') or {}).get('value') or ''),
            'transformations': len(indicator.get('transformations') or []),
        },
        'event': {
            'id': event.get('record_id'),
            'type': event.get('record_type'),
            'state': event.get('truth_state'),
            'source': (event.get('source') or {}).get('publisher'),
            'fingerprint': len((event.get('fingerprint') or {}).get('value') or ''),
        },
        'panelVisible': page.is_visible('#recordTruthPanel'),
        'downloadEnabled': not page.is_disabled('#recordTruthDownload'),
        'consoleApi': page.evaluate("Boolean(window.SCSIRecordProvenanceV3238?.exportManifest)"),
    }


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for the record-provenance gate.')
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for the record-provenance gate.')
        return 2

    results: list[dict[str, object]] = []
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=browser_path, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu-sandbox'])
        html, _ = document('disabled')
        direct = browser.new_page(viewport={'width': 1280, 'height': 900})
        direct.on('pageerror', lambda error: errors.append(f'direct:{error}'))
        direct.set_content(html, wait_until='domcontentloaded', timeout=45000)
        results.append(exercise(direct, 'direct'))
        direct.close()

        outer = browser.new_page(viewport={'width': 1280, 'height': 920})
        outer.set_content('<iframe id="gate" style="width:1180px;height:820px;border:0"></iframe>')
        frame = outer.query_selector('#gate').content_frame()
        assert frame is not None
        frame.set_content(html, wait_until='domcontentloaded', timeout=45000)
        results.append(exercise(frame, 'iframe'))
        outer.close()
        browser.close()

    assert not errors, errors
    for result in results:
        assert result['layer']['type'] == 'map_layer' and result['layer']['state'] == 'context_only', result
        assert result['layer']['fingerprint'] == 64, result
        assert result['indicator']['id'] == 'indicator:KEN:SP.POP.TOTL', result
        assert result['indicator']['type'] == 'indicator' and result['indicator']['state'] == 'historical_snapshot', result
        assert result['indicator']['year'] == 2023 and result['indicator']['fingerprint'] == 64, result
        assert result['indicator']['transformations'] >= 4, result
        assert result['event']['id'] == 'event:browser-gate-event' and result['event']['type'] == 'event', result
        assert result['event']['state'] == 'observed' and result['event']['source'] == 'USGS', result
        assert result['event']['fingerprint'] == 64, result
        assert result['panelVisible'] is True and result['downloadEnabled'] is True and result['consoleApi'] is True, result
    print(json.dumps({'browser': browser_path, 'results': results, 'errors': errors}, indent=2))
    print('PASS: v4.11.0 opened map-layer, indicator, and event record truth with dates, transformations, source disclosure, and stable fingerprints in direct and iframe modes.')
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
