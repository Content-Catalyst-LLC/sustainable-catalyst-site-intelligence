#!/usr/bin/env python3
from __future__ import annotations

import traceback
import json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='3.23.7.2'
def browser_path():
 candidates=[os.getenv('SC_SI_CHROMIUM',''),shutil.which('chromium') or '',shutil.which('google-chrome') or '',shutil.which('google-chrome-stable') or '','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Chromium.app/Contents/MacOS/Chromium']
 return next((x for x in candidates if x and Path(x).is_file() and os.access(x,os.X_OK)),None)
def main():
 executable=browser_path()
 if not executable:print('ERROR: Chromium or Chrome is required for the production-soak browser gate.',file=sys.stderr);return 2
 try:from playwright.sync_api import sync_playwright
 except ImportError:print('ERROR: Playwright is required for the production-soak browser gate.',file=sys.stderr);return 2
 sys.path.insert(0,str(ROOT/'scripts'));import browser_complete_shell_gate_v32362 as shell
 results={};errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
  for mode in ('disabled','failure'):
   html,_=shell.document(mode);page=browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e,m=mode:errors.append(f'{m}:{e}'))
   page.set_content(html,wait_until='domcontentloaded',timeout=45000)
   page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=7000)
   ready_ms=page.evaluate("performance.now()")
   assert ready_ms<7000,(mode,ready_ms)
   for _ in range(3):
    for route in ('science','overview','country','overview'):
     page.locator(f'[data-route="{route}"]').click();page.wait_for_timeout(80)
   page.wait_for_timeout(1500)
   snapshot=page.evaluate("""()=>({ready:document.querySelector('#app')?.classList.contains('app-ready'),launchHidden:document.querySelector('#launchScreen')?.classList.contains('hidden'),startup:window.SCSIStartupStabilityV32364?.getState?.(),bootstrap:window.SCSIBootstrapV32361?.getState?.(),routeBusy:document.documentElement.dataset.scsiRouteBusy,reloads:performance.getEntriesByType('navigation')[0]?.type})""")
   assert snapshot['ready'] and snapshot['launchHidden'],snapshot
   assert snapshot['bootstrap']['automaticReloads']==0,snapshot
   assert snapshot['startup']['routeTransitions']>=1,snapshot
   results[mode]={'readyMs':ready_ms,'snapshot':snapshot};page.close()
  browser.close()
 assert not errors,errors
 print(json.dumps({'browser':executable,'results':results},indent=2));print('PASS: v3.23.7.2 opened its shell without network dependency, serialized route churn, and performed no service-worker reload.');return 0
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
