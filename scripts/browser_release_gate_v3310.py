#!/usr/bin/env python3
from __future__ import annotations
import json, os, traceback
from browser_complete_shell_gate_v32362 import document, find_browser, snapshot, assert_ready

ROUTES=['overview','country','compare','earth','spatial','scenarios','research','monitoring','publishing','workspaces','governance','sources']

def exercise(page,label):
    page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
    page.wait_for_function("window.SCSIProductionAssuranceV3310 && document.documentElement.dataset.productionAssurance === 'ready'",timeout=15000)
    initial=snapshot(page); assert_ready(label,initial)
    # Exercise the native country catalog programmatically without opening browser chrome.
    before=page.locator('#countrySelect option').count()
    page.select_option('#countrySelect','BRA')
    page.wait_for_function("document.querySelector('#countrySelect').value === 'BRA'",timeout=5000)
    if page.locator('#dataTruthToggle').count(): page.click('#dataTruthToggle')
    page.wait_for_timeout(200)
    badge=page.locator('#dataTruthBadge').text_content() if page.locator('#dataTruthBadge').count() else ''
    country={'before':before,'value':page.locator('#countrySelect').input_value()}
    failures=[]
    for route in ROUTES:
        loc=page.locator(f'.nav-item[data-route="{route}"]')
        if not loc.count(): failures.append(f'missing:{route}'); continue
        try:
            page.evaluate('(route)=>window.SCSIRouterV3228.navigate(route)',route); page.wait_for_timeout(45)
        except Exception as exc: failures.append(f'{route}:{exc}')
    final=snapshot(page)
    return {'label':label,'scripts':final['executedScripts'],'expected':final['expectedScripts'],'countryOptions':country['before'],'country':country['value'],'badge':badge,'routeFailures':failures,'productionAssurance':final.get('productionAssuranceReady',False),'ready':final['ready']}

def main():
    path=find_browser()
    if not path: print('ERROR: Chrome/Chromium required.'); return 2
    from playwright.sync_api import sync_playwright
    errors=[]; results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        html,_=document('disabled')
        page=browser.new_page(viewport={'width':1360,'height':940}); page.on('pageerror',lambda e:errors.append(f'direct:{e}')); page.set_content(html,wait_until='domcontentloaded',timeout=45000); results.append(exercise(page,'direct')); page.close()
        outer=browser.new_page(viewport={'width':1360,'height':960}); outer.set_content('<iframe id="g" style="width:1240px;height:880px;border:0"></iframe>'); frame=outer.query_selector('#g').content_frame(); frame.set_content(html,wait_until='domcontentloaded',timeout=45000); results.append(exercise(frame,'iframe')); outer.close(); browser.close()
    assert not errors,errors
    for r in results:
        assert r['ready'] and r['productionAssurance'] and r['scripts']==r['expected'] and r['expected']>=47,r
        assert r['countryOptions']>=170 and r['country']=='BRA' and 'BRA' in (r['badge'] or ''),r
        assert not r['routeFailures'],r
    print(json.dumps({'browser':path,'results':results,'errors':errors},indent=2)); print('PASS: v4.11.0 composite release gate verified complete shell, production assurance, global country selection, route churn, and iframe behavior.'); return 0
if __name__=='__main__':
    try: status=int(main())
    except BaseException: traceback.print_exc(); status=1
    try:
        import sys; sys.stdout.flush(); sys.stderr.flush()
    finally: os._exit(status)
