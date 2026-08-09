#!/usr/bin/env python3
from __future__ import annotations
import json, os, traceback
from browser_complete_shell_gate_v32362 import document, find_browser


def exercise(page,label):
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
    page.evaluate("()=>window.SCSIRouterV3228.navigate('alerts')")
    page.wait_for_function("window.SCSIMonitoringOperationsV3280 && document.documentElement.dataset.monitoringOperations === 'ready'",timeout=15000)
    page.wait_for_timeout(250)
    return page.evaluate("""(label)=>{const snap=window.SCSIMonitoringOperationsV3280.snapshot();return{label,panel:!!document.querySelector('#monitoringOperationsPanel'),state:document.querySelector('#monitoringOpsState')?.textContent,alertStates:Number(document.querySelector('#monitoringOpsAlertStates')?.textContent||0),watchTypes:Number(document.querySelector('#monitoringOpsWatchTypes')?.textContent||0),review:document.querySelector('#monitoringOperationsPanel')?.textContent.includes('Review gated'),emergency:document.querySelector('#monitoringOperationsPanel')?.textContent.includes('Disabled'),country:snap.country||'',scripts:(window.__executedScripts||[]).filter(s=>String(s).includes('monitoring-operations-v3280.js')).length}}""",label)


def main():
    path=find_browser()
    if not path: print('ERROR: Chrome/Chromium required.'); return 2
    from playwright.sync_api import sync_playwright
    errors=[];results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        html,_=document('disabled')
        page=browser.new_page(viewport={'width':1360,'height':940});page.on('pageerror',lambda e:errors.append(f'direct:{e}'));page.set_content(html,wait_until='domcontentloaded',timeout=45000);results.append(exercise(page,'direct'));page.close()
        outer=browser.new_page(viewport={'width':1360,'height':960});outer.set_content('<iframe id="g" style="width:1240px;height:880px"></iframe>');frame=outer.query_selector('#g').content_frame();frame.set_content(html,wait_until='domcontentloaded',timeout=45000);results.append(exercise(frame,'iframe'));outer.close();browser.close()
    assert not errors,errors
    for r in results:
        assert r['panel'] and r['state']=='Ready' and r['alertStates']==5 and r['watchTypes']==4 and r['review'] and r['emergency'] and r['country']=='KEN' and r['scripts']==1,r
    print(json.dumps({'browser':path,'results':results,'errors':errors},indent=2));print('PASS: v4.5.0 monitoring, digest, and early-warning operations rendered in direct and iframe modes.');return 0
if __name__=='__main__':
    try: status=int(main())
    except BaseException: traceback.print_exc();status=1
    try:
        import sys;sys.stdout.flush();sys.stderr.flush()
    finally: os._exit(status)
