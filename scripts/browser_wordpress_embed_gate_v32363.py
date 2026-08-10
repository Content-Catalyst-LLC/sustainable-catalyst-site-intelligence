#!/usr/bin/env python3
"""Mandatory long-page WordPress embed stability gate for Site Intelligence v4.15.0."""
from __future__ import annotations

import traceback

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WP = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence"
VERSION = "4.15.0"


def browser_path() -> str | None:
    candidates = [
        os.getenv("SC_SI_CHROMIUM", ""),
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("google-chrome") or "",
        shutil.which("google-chrome-stable") or "",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def host_document() -> str:
    css = (WP / "assets/sc-site-intelligence.css").read_text(encoding="utf-8")
    js = (WP / "assets/sc-site-intelligence.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><style>{css}</style></head><body>
<section style=\"height:1800px;padding:40px\"><h1>Long WordPress page before application</h1></section>
<main class=\"ccp-site-intelligence-public\">
<div class=\"ccp-status-item\"><span class=\"ccp-status-label\">Current version</span><strong>3.22.0</strong></div>
<div class=\"ccp-release-bar\"><strong>Site Intelligence v3.22.0 - stale</strong></div>
<div class=\"scsi-standalone-app scsi-fixed-application-viewport\" data-scsi-fixed-app data-scsi-embed-mode=\"fixed\" data-scsi-fixed-height=\"1100\" data-scsi-release=\"4.15.0\" style=\"--scsi-fixed-app-height:1100px\">
<div class=\"scsi-app-loading\">Opening Site Intelligence...</div>
<iframe id=\"appframe\" data-scsi-embed-frame data-scsi-embed-mode=\"fixed\" data-scsi-fixed-height=\"1100\" data-scsi-min-height=\"1100\" data-scsi-mobile-min-height=\"1100\" data-scsi-max-height=\"1100\" style=\"width:100%;height:1100px;min-height:1100px;max-height:1100px;border:0;display:block\"></iframe>
<p class=\"scsi-embed-fallback\"><a href=\"https://example.invalid/app/\">Open in new tab</a></p></div></main>
<section style=\"height:2200px;padding:40px\"><h2>Long WordPress page after application</h2></section>
<script>window.SCSiteIntelligence={{version:\"4.15.0\",restBase:\"\",backendUrl:\"https://example.invalid\"}};</script>
<script>{js}</script></body></html>"""


def child_document() -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    import browser_complete_shell_gate_v32362 as complete_shell

    html, _count = complete_shell.document("disabled")
    force = "<script>window.SCSI_FORCE_WORDPRESS_EMBED=true;</script>"
    return html.replace("<head>", "<head>" + force, 1)


def snapshot(page):
    return page.evaluate(
        """()=>{const f=document.querySelector('#appframe'),w=f.closest('[data-scsi-fixed-app]'),r=f.getBoundingClientRect();return{frameHeight:Math.round(r.height),wrapperHeight:Math.round(w.getBoundingClientRect().height),scrollHeight:document.documentElement.scrollHeight,scrollY:Math.round(scrollY),release:w.dataset.scsiRelease,mode:f.dataset.scsiEmbedMode,publicVersion:document.querySelector('.ccp-status-item strong')?.textContent,bar:document.querySelector('.ccp-release-bar strong')?.textContent}}"""
    )


def main() -> int:
    executable = browser_path()
    if not executable:
        print("ERROR: Chromium or Chrome is required for the WordPress embed gate.", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for the WordPress embed gate.", file=sys.stderr)
        return 2

    errors: list[str] = []
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.set_content(host_document(), wait_until="domcontentloaded", timeout=45000)
        frame = page.query_selector("#appframe").content_frame()
        frame.set_content(child_document(), wait_until="domcontentloaded", timeout=45000)
        frame.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=30000)
        frame.wait_for_function("document.querySelector('#launchScreen')?.classList.contains('hidden')", timeout=12000)
        page.wait_for_timeout(800)

        before = snapshot(page)
        assert before["frameHeight"] == 1100 and before["wrapperHeight"] == 1100, before
        assert before["release"] == VERSION and before["mode"] == "fixed", before
        assert before["publicVersion"] == VERSION, before

        child_state = frame.evaluate(
            """()=>({embed:document.documentElement.dataset.scsiEmbedMode,isolated:window.SCSI_FIXED_WORDPRESS_EMBED===true,heightMessages:window.SCSIEmbedIsolationV32363?.getState?.().heightMessagesEnabled,ready:document.querySelector('#app')?.classList.contains('app-ready'),scripts:(window.__executedScripts||[]).length,expected:Number(window.__expectedScriptCount||0)})"""
        )
        assert child_state["embed"] == "wordpress-fixed", child_state
        assert child_state["isolated"] is True and child_state["heightMessages"] is False and child_state["ready"] is True, child_state
        assert child_state["scripts"] == child_state["expected"] and child_state["expected"] >= 30, child_state

        page.evaluate("scrollTo(0,2100)")
        page.wait_for_timeout(200)
        anchor = snapshot(page)
        for width, height in [(1280, 820), (1100, 760), (1440, 900), (1180, 840), (1440, 900)]:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(120)
        page.evaluate("y=>scrollTo(0,y)", anchor["scrollY"])
        page.wait_for_timeout(150)
        post_resize = snapshot(page)
        frame.evaluate(
            """()=>{for(let i=0;i<120;i++){const n=document.createElement('span');n.textContent='probe';document.querySelector('#overviewStudio')?.append(n);n.remove()}document.querySelector('[data-route="science"]')?.click();document.querySelector('[data-route="overview"]')?.click();window.dispatchEvent(new Event('resize'));window.dispatchEvent(new Event('orientationchange'));}"""
        )
        page.wait_for_timeout(900)
        after = snapshot(page)
        assert after["frameHeight"] == 1100 and after["wrapperHeight"] == 1100, (before, after)
        assert abs(after["scrollHeight"] - before["scrollHeight"]) <= 4, (before, after)
        assert abs(after["scrollY"] - post_resize["scrollY"]) <= 4, (post_resize, after)
        assert frame.evaluate("document.querySelector('#app').classList.contains('app-ready')") is True
        browser.close()

    actionable = [
        message
        for message in console_errors
        if not any(token in message.lower() for token in ("failed to load resource", "net::err_", "favicon"))
    ]
    assert not errors, errors
    assert not actionable, actionable
    print(json.dumps({"browser": executable, "before": before, "anchor": anchor, "postResize": post_resize, "after": after, "child": child_state, "consoleErrors": console_errors}, indent=2))
    print("PASS: v4.15.0 fixed WordPress application viewport remained 1100px and the long host page did not jump during route, mutation, scroll, or viewport changes.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(status)
