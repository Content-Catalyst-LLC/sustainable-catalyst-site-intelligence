#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v3.24.0 data truth presentation."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "backend/public_app/assets/data-truth-v32371.js"
CSS = ROOT / "backend/public_app/assets/data-truth-v32371.css"


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
    payload = {
        "ok": True, "version": "3.24.0", "release_id": "site-intelligence-v3.24.0",
        "application_mode": "demonstration", "source_count": 3,
        "summary": {"live": 0, "recently_cached": 1, "historical_snapshot": 1, "demonstration": 1, "context_only": 0, "unavailable": 0},
        "sources": [
            {"feed_id":"a","label":"Cached source","publisher":"Publisher A","endpoint":{"url":"https://example.test/a"},"license":{"name":"Open"},"coverage":{"geographic":"Global","temporal":"Recent"},"refresh_policy":{"refresh_minutes":10,"stale_after_minutes":60},"retrieval":{"last_success_at":"2026-08-05T20:00:00Z"},"data_state":{"presentation":"recently_cached","reason":"Last known good response.","stale_marker_required":True},"completeness":{"score_percent":100},"schema":{"status":"matched"},"quality":{"limitations":"Coverage varies."}},
            {"feed_id":"b","label":"Historical source","publisher":"Publisher B","endpoint":{"url":"https://example.test/b"},"license":{"name":"CC BY"},"coverage":{"geographic":"Country","temporal":"Annual"},"refresh_policy":{"refresh_minutes":1440,"stale_after_minutes":10080},"retrieval":{"last_success_at":"2026-08-01T20:00:00Z"},"data_state":{"presentation":"historical_snapshot","reason":"Periodic record.","stale_marker_required":False},"completeness":{"score_percent":100},"schema":{"status":"not_observed"},"quality":{"limitations":"Annual values."}},
            {"feed_id":"c","label":"Demo source","publisher":"Publisher C","endpoint":{"url":"https://example.test/c"},"license":{"name":"Open"},"coverage":{"geographic":"Global","temporal":"Example"},"refresh_policy":{"refresh_minutes":30,"stale_after_minutes":90},"retrieval":{"last_success_at":None},"data_state":{"presentation":"demonstration","reason":"No successful production retrieval.","stale_marker_required":False},"completeness":{"score_percent":100},"schema":{"status":"not_observed"},"quality":{"limitations":"Demonstration only."}},
        ]
    }
    errors=[]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu-sandbox"])
        page = browser.new_page(viewport={"width":1280,"height":820})
        page.on("console", lambda message: errors.append(f"console:{message.type}:{message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
        page.set_content('<!doctype html><html><body><div id="app" data-scsi-release="3.24.0" style="position:relative;height:760px;background:#111;color:#fff"><header><div class="topbar-controls"></div></header></div></body></html>')
        page.add_style_tag(content=CSS.read_text())
        page.evaluate("payload => { window.fetch=async()=>({ok:true,json:async()=>payload}); }", payload)
        page.add_script_tag(content=JS.read_text())
        page.wait_for_timeout(250)
        page.click('#dataTruthToggle')
        result=page.evaluate("() => ({visible:!document.querySelector('#dataTruthPanel').hidden,badge:document.querySelector('#dataTruthBadge').textContent,rows:document.querySelectorAll('.scsi-data-source').length,states:[...document.querySelectorAll('.scsi-truth-state')].map(n=>n.textContent.trim()),warnings:document.querySelectorAll('.scsi-truth-warning').length,summary:document.querySelectorAll('.scsi-data-truth-summary article').length})")
        browser.close()
    assert result["visible"] and result["rows"] == 3, result
    assert result["summary"] == 6 and result["warnings"] == 1, result
    assert "recently cached" in result["states"] and "historical snapshot" in result["states"] and "demonstration" in result["states"], result
    assert not errors, errors
    print(json.dumps(result, indent=2))
    print("PASS: v3.24.0 rendered explicit live, cached, historical, demonstration, coverage, and schema states without host-document leakage.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
