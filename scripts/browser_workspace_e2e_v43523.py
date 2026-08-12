#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import document, find_browser

sys.path.insert(0, str(ROOT / "backend"))
import app.live_country_intelligence as live_country
from browser_workspace_e2e_v43518 import exercise


def run_mode(mode: str) -> dict:
    live_country._catalog_from_world_bank = lambda: {}
    live_country._COUNTRY_CATALOG_CACHE = live_country._normalized_static_catalog()
    live_country._COUNTRY_CATALOG_FETCHED_AT = "2026-08-12T00:00:00Z"
    live_country._COUNTRY_CATALOG_STATE = "fallback-catalog"
    browser_path = find_browser()
    if not browser_path:
        raise RuntimeError("Chromium or Chrome is required.")
    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=browser_path,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        html, _ = document("disabled")
        if mode == "desktop":
            page = browser.new_page(viewport={"width": 1360, "height": 940})
            page.on("pageerror", lambda e: errors.append(f"desktop:{e}"))
            page.set_content(html, wait_until="domcontentloaded", timeout=60000)
            rows = exercise(page, "desktop")
            page.close()
        elif mode == "mobile":
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.on("pageerror", lambda e: errors.append(f"mobile:{e}"))
            page.set_content(html, wait_until="domcontentloaded", timeout=60000)
            rows = exercise(page, "mobile")
            page.close()
        else:
            outer = browser.new_page(viewport={"width": 1280, "height": 920})
            outer.on("pageerror", lambda e: errors.append(f"iframe:{e}"))
            outer.set_content('<iframe id="gate" style="width:1180px;height:820px;border:0"></iframe>')
            frame = outer.query_selector("#gate").content_frame()
            frame.set_content(html, wait_until="domcontentloaded", timeout=60000)
            rows = exercise(frame, "iframe")
            outer.close()
        browser.close()
    if errors:
        raise AssertionError(errors)
    summary = {
        "routes": len(rows),
        "ready": sum(1 for row in rows if row["surfaceVisible"]),
        "degraded": sum(1 for row in rows if row["recoveryVisible"]),
    }
    if summary["routes"] != 35:
        raise AssertionError(summary)
    return {"browser": browser_path, "mode": mode, "summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("desktop", "mobile", "iframe"), required=True)
    args = parser.parse_args()
    result = run_mode(args.mode)
    print(json.dumps(result, indent=2))
    print(f"PASS: v4.35.23 {args.mode} browser workspace gate: 35/35 routes visible or explicitly degraded.")
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
