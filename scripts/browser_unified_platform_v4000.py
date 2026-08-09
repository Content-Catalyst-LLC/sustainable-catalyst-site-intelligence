#!/usr/bin/env python3
from __future__ import annotations
import json, os, traceback
from browser_complete_shell_gate_v32362 import document, find_browser, snapshot, assert_ready

def exercise(page,label):
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
    page.wait_for_function("window.SCSIUnifiedPlatformV4000 && document.documentElement.dataset.v4Navigation === 'ready'",timeout=12000)
    initial=snapshot(page); assert_ready(label,initial)
    groups=page.locator('.v4000-nav-group').count(); routes=page.locator('.v4000-nav-group .nav-item[data-route]').count()
    page.locator('.v4000-nav-group[data-area="analysis"] > summary').click()
    page.locator('.v4000-nav-group[data-area="analysis"] .nav-item[data-route="compare"]').click()
    page.wait_for_function("window.SCSIRouterV3228?.current?.() === 'compare'",timeout=6000)
    page.wait_for_timeout(80)
    analysis_open=page.locator('.v4000-nav-group[data-area="analysis"]').get_attribute('open') is not None
    analysis_active=page.locator('.v4000-nav-group[data-area="analysis"]').get_attribute('data-active')
    page.locator('.v4000-nav-group[data-area="evidence-research"] > summary').click()
    page.locator('.v4000-nav-group[data-area="evidence-research"] .nav-item[data-route="platform"]').click()
    page.wait_for_function("window.SCSIRouterV3228?.current?.() === 'platform'",timeout=6000)
    page.wait_for_function("document.querySelector('#v4000PlatformState')?.textContent.trim().length > 0",timeout=6000)
    metrics=page.evaluate("()=>({areas:document.querySelector('#v4000AreaCount')?.textContent,routes:document.querySelector('#v4000RouteCount')?.textContent,contracts:document.querySelector('#v4000ContractCount')?.textContent,card:Boolean(document.querySelector('#unifiedPublicPlatformV4000'))})")
    return {'label':label,'groups':groups,'routes':routes,'analysisOpen':analysis_open,'analysisActive':analysis_active,'metrics':metrics,'scripts':initial['executedScripts'],'expected':initial['expectedScripts']}

def main():
    path=find_browser()
    if not path: print('ERROR: Chrome/Chromium required.'); return 2
    from playwright.sync_api import sync_playwright
    errors=[];results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        html,_=document('disabled')
        page=browser.new_page(viewport={'width':1360,'height':940});page.on('pageerror',lambda e:errors.append(f'direct:{e}'));page.set_content(html,wait_until='domcontentloaded',timeout=45000);results.append(exercise(page,'direct'));page.close()
        outer=browser.new_page(viewport={'width':1360,'height':960});outer.set_content('<iframe id="g" style="width:1240px;height:880px;border:0"></iframe>');frame=outer.query_selector('#g').content_frame();frame.set_content(html,wait_until='domcontentloaded',timeout=45000);results.append(exercise(frame,'iframe'));outer.close();browser.close()
    assert not errors,errors
    for r in results:
        assert r['groups']==6 and r['routes']==35,r
        assert r['analysisOpen'] and r['analysisActive']=='true',r
        assert r['metrics']=={'areas':'6','routes':'35','contracts':'6','card':True},r
        assert r['scripts']==r['expected'] and r['expected']>=48,r
    print(json.dumps({'browser':path,'results':results,'errors':errors},indent=2))
    print('PASS: v4.2.0 grouped navigation and unified platform contract rendered in direct and iframe modes.')
    return 0
if __name__=='__main__':
    try: status=int(main())
    except BaseException: traceback.print_exc();status=1
    try:
        import sys;sys.stdout.flush();sys.stderr.flush()
    finally: os._exit(status)
