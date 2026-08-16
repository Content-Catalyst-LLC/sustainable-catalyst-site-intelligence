#!/usr/bin/env python3
"""Browser certification for v4.36.0 R4 Science/Ocean route ownership and recovery."""
from __future__ import annotations
import json, os, sys, traceback
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from browser_complete_shell_gate_v32362 import document, find_browser
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import app


def main()->int:
    browser_path=find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for the v4.36.0 R4 browser gate.'); return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for the v4.36.0 R4 browser gate.'); return 2
    client=TestClient(app)
    html,_=document('disabled')
    science_js=(ROOT/'backend/public_app/assets/science-v240.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route_handler(route):
            parsed=urlsplit(route.request.url)
            if parsed.path.endswith('/app/assets/science-v240.js'):
                route.fulfill(status=200,content_type='application/javascript',body=science_js); return
            if parsed.path.startswith('/public/'):
                target=parsed.path+('?' + parsed.query if parsed.query else '')
                response=client.get(target)
                route.fulfill(status=response.status_code,content_type=response.headers.get('content-type','application/json'),body=response.content); return
            route.continue_()
        page.route('**/*',route_handler)
        page.set_content(html,wait_until='domcontentloaded',timeout=60000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
        page.wait_for_function("window.SCSIRouterV3228 && window.SCSIProductionTruthV3231",timeout=12000)
        # Featured science systems must survive navigation consolidation and remain visible.
        page.wait_for_function("document.documentElement.dataset.v4Navigation === 'ready'",timeout=10000)
        featured=page.evaluate("""()=>({
          labels:[...document.querySelectorAll('#primaryNavigation .v4000-nav-featured .nav-item span')].map(x=>x.textContent.trim()),
          ocean:!!document.querySelector('#primaryNavigation [data-ocean-entry=\"hub\"]'),
          space:!!document.querySelector('#primaryNavigation [data-space-entry=\"hub\"]')
        })""")
        assert featured['ocean'] and featured['space'],featured
        assert featured['labels']==['Ocean','Space'],featured
        # Deliberately simulate the stale/missing controller condition reported in production,
        # then enter Space directly from the persistent featured control.
        page.evaluate("()=>{delete window.SCScienceV240; return true}")
        page.locator('#primaryNavigation [data-space-entry="hub"]').click()
        page.wait_for_function("window.SCScienceV240?.status?.().repair === '4.36.0-r4'",timeout=10000)
        page.wait_for_function("!document.querySelector('#scienceStudio')?.hidden",timeout=10000)
        page.wait_for_function("document.querySelector('#scienceWorkspaceSelect')?.value === 'space'",timeout=10000)
        page.wait_for_selector('[data-science-local-action="seti"]',state='visible',timeout=5000)
        science=page.evaluate("""()=>({
          route:window.SCSIRouterV3228.current(),
          repair:window.SCScienceV240?.status?.().repair||'',
          domain:window.SCScienceV240?.status?.().domain||'',
          options:[...document.querySelectorAll('#scienceWorkspaceSelect option')].map(x=>x.textContent),
          visible:!document.querySelector('#scienceStudio')?.hidden,
          spaceActive:document.querySelector('#primaryNavigation [data-space-entry=\"hub\"]')?.classList.contains('active')||false,
          spaceCards:document.querySelectorAll('#scienceWorkspaceCards .science-workspace-card').length
        })""")
        assert science['route']=='science' and science['repair']=='4.36.0-r4' and science['visible'],science
        assert science['domain']=='space' and science['spaceActive'] and science['spaceCards']==6,science
        assert science['options']==['Earth','Ocean','Space'],science
        # Ocean must be equally prominent and transfer route ownership cleanly.
        page.locator('#primaryNavigation [data-ocean-entry="hub"]').click()
        page.wait_for_function("document.querySelector('#oceanObservationStudio')?.dataset.oceanHydrationState === 'ready'",timeout=20000)
        page.wait_for_function("document.querySelectorAll('#oceanObservationStudio [data-ocean-card]').length === 11",timeout=10000)
        page.wait_for_function("window.SCSIProductionTruthV3231.current().route === 'earth'",timeout=10000)
        page.wait_for_function("window.SCSIProductionTruthV3231.current().state === 'ready'",timeout=10000)
        ocean=page.evaluate("""()=>({
          route:window.SCSIRouterV3228.current(),
          mode:new URLSearchParams(location.search).get('oceanMode')||'',
          visible:!document.querySelector('#oceanObservationStudio')?.hidden,
          hydration:document.querySelector('#oceanObservationStudio')?.dataset.oceanHydrationState||'',
          owner:document.querySelector('#oceanObservationStudio')?.dataset.oceanWorkspaceOwner||'',
          cards:document.querySelectorAll('#oceanObservationStudio [data-ocean-card]').length,
          truth:window.SCSIProductionTruthV3231.current(),
          title:document.querySelector('#viewTitle')?.textContent||''
        })""")
        assert ocean['route']=='earth',ocean
        assert ocean['visible'] and ocean['hydration']=='ready' and ocean['cards']==11,ocean
        assert ocean['owner']=='earth:ocean',ocean
        assert ocean['truth']['state']=='ready',ocean
        # Space must remain one click away after Ocean.
        page.locator('#primaryNavigation [data-space-entry="hub"]').click()
        page.wait_for_function("document.querySelector('#scienceWorkspaceSelect')?.value === 'space' && !document.querySelector('#scienceStudio')?.hidden",timeout=10000)
        page.wait_for_selector('[data-science-local-action="seti"]',state='visible',timeout=5000)
        space=page.evaluate("""()=>({
          cards:document.querySelectorAll('#scienceWorkspaceCards .science-workspace-card').length,
          actions:[...document.querySelectorAll('#scienceWorkspaceCards [data-science-local-action]')].map(x=>x.dataset.scienceLocalAction),
          active:document.querySelector('#primaryNavigation [data-space-entry=\"hub\"]')?.classList.contains('active')||false
        })""")
        assert space['cards']==6 and space['active'],space
        assert {'orbital-earth','planetary','astronomy','solar-system','exoplanets','seti'}==set(space['actions']),space
        browser.close()
    assert not errors,errors
    print(json.dumps({'browser':browser_path,'featured':featured,'science':science,'ocean':ocean,'space':space,'errors':errors},indent=2))
    print('PASS: v4.36.0 R4 keeps Ocean and Space first-class, recovers a missing Science controller, certifies six Space workspaces, transfers route ownership to Ocean, and certifies 11 visible marine systems.')
    return 0

if __name__=='__main__':
    try: status=int(main())
    except BaseException:
        traceback.print_exc(); status=1
    try: sys.stdout.flush(); sys.stderr.flush()
    finally: os._exit(status)
