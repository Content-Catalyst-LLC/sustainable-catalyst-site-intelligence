#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from browser_complete_shell_gate_v32362 import document, find_browser

ROUTES = [
    "overview","global","events","alerts","country","dossiers","economics","law","science","humanitarian","resources","thematic",
    "compare","spatial","earth","harmonization","models","scenarios","platform","observatory","research","evidence","graph","sources","saved",
    "briefing","publishing","monitoring","workspaces","integration","workflows","federation","governance","experience","launch",
]


def exercise(page, label: str):
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=25000)
    page.wait_for_function("window.SCSIWorkspaceReliabilityV43518 && window.SCSIRouterV3228", timeout=12000)
    rows = []
    for route in ROUTES:
        page.evaluate("r=>window.SCSIRouterV3228.navigate(r)", route)
        page.wait_for_function("document.documentElement.dataset.scsiRouteBusy !== 'true'", timeout=15000)
        page.wait_for_timeout(35)
        row = page.evaluate("""r=>{const api=window.SCSIWorkspaceReliabilityV43518;const selector=api.surfaces[r];const surface=document.querySelector(selector);const recovery=document.querySelector(`#routePanel[data-workspace-recovery="${r}"]`);const visible=e=>!!e&&!e.hidden&&getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden';return{route:r,title:document.querySelector('#viewTitle')?.textContent?.trim()||'',selector,surfaceVisible:visible(surface),recoveryVisible:visible(recovery),unavailable:[...document.querySelectorAll('#routePanel h2')].some(e=>visible(e)&&e.textContent.trim()==='View unavailable'),busy:document.documentElement.dataset.scsiRouteBusy||'',state:api.status(r)?.state||'',scrollWidth:document.documentElement.scrollWidth,innerWidth:innerWidth}}""", route)
        assert row["title"], (label, row)
        assert row["surfaceVisible"] or row["recoveryVisible"], (label, row)
        assert not row["unavailable"], (label, row)
        assert row["busy"] != "true", (label, row)
        assert row["scrollWidth"] <= row["innerWidth"] + 3, (label, row)
        rows.append(row)
    return rows


def main():
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required.", file=sys.stderr)
        return 2
    from playwright.sync_api import sync_playwright
    errors=[]; results={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        html,_=document('disabled')
        for label, viewport in (("desktop", {"width":1360,"height":940}), ("mobile", {"width":390,"height":844})):
            page=browser.new_page(viewport=viewport)
            page.on('pageerror', lambda e,l=label: errors.append(f"{l}:{e}"))
            page.set_content(html,wait_until='domcontentloaded',timeout=60000)
            results[label]=exercise(page,label)
            page.close()
        outer=browser.new_page(viewport={"width":1280,"height":920})
        outer.set_content('<iframe id="gate" style="width:1180px;height:820px;border:0"></iframe>')
        frame=outer.query_selector('#gate').content_frame();frame.set_content(html,wait_until='domcontentloaded',timeout=60000)
        results['iframe']=exercise(frame,'iframe')
        outer.close();browser.close()
    assert not errors, errors
    summary={mode:{"routes":len(rows),"ready":sum(1 for r in rows if r['surfaceVisible']),"degraded":sum(1 for r in rows if r['recoveryVisible'])} for mode,rows in results.items()}
    assert all(v['routes']==35 for v in summary.values()), summary
    print(json.dumps({"browser":browser_path,"summary":summary},indent=2))
    print("PASS: v4.35.23 all 35 registered workspaces open visibly or explicitly degraded across desktop, mobile, and iframe modes.")
    return 0

if __name__ == "__main__":
    try: status=int(main())
    except BaseException: traceback.print_exc(); status=1
    try: sys.stdout.flush(); sys.stderr.flush()
    finally: os._exit(status)
