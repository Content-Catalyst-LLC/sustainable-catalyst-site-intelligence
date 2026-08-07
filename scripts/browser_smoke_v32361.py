#!/usr/bin/env python3
"""Network-independent Chromium validation for v3.28.0 bootstrap ownership and loading recovery."""
from __future__ import annotations
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/bootstrap-v32361.js').read_text(encoding='utf-8')

def shell(deadline=600):
    return f'''<!doctype html><html><body><div id="launchScreen"><p id="launchMessage">Opening</p><span id="launchProgressBar"></span><button id="launchRetry" hidden>Retry</button></div><div id="app" class="app-loading" data-scsi-release="3.28.0" data-scsi-startup-deadline-ms="{deadline}"></div></body></html>'''

def fake_worker(controller=False, waiting=False, fail=False):
    return f'''(() => {{
      const bus=new EventTarget();
      const active={{postMessage(){{}}}};
      const wait={{postMessage(message){{window.__activationMessage=message}}}};
      const reg=new EventTarget();reg.waiting={str(waiting).lower()}?wait:null;reg.installing=null;reg.active=active;reg.update=()=>Promise.resolve();
      bus.controller={('{}' if controller else 'null')};
      bus.register=async()=>{{{'throw new Error("registration failed")' if fail else 'return reg'}}};
      Object.defineProperty(navigator,'serviceWorker',{{configurable:true,value:bus}});
    }})()'''

def snapshot(page):
    return page.evaluate("""() => ({hidden:document.querySelector('#launchScreen').classList.contains('hidden'),startup:document.querySelector('#app').dataset.startupState||'',ready:document.querySelector('#app').classList.contains('app-ready'),owner:Boolean(window.SCSIBootstrapV32361),worker:window.SCSIBootstrapV32361?.getState().workerState||'',message:document.querySelector('#launchMessage').textContent})""")

def main():
    chromium=shutil.which('chromium') or shutil.which('chromium-browser')
    if not chromium:
        print('SKIP: Chromium unavailable.');return 0
    try: from playwright.sync_api import sync_playwright
    except ImportError:
        print('SKIP: Playwright unavailable.');return 0
    errors=[];results={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        # No existing worker: rendering does not wait for registration.
        page=browser.new_page();page.on('pageerror',lambda e:errors.append(f'no-worker:{e}'));page.set_content(shell());page.evaluate(fake_worker());page.add_script_tag(content=JS);page.evaluate("setTimeout(()=>window.dispatchEvent(new CustomEvent('scsi:application-ready',{detail:{version:'3.28.0',state:'ready'}})),30)");page.wait_for_timeout(120);results['no_existing_worker']=snapshot(page);page.close()
        # Older/current controller with waiting update: update can activate but rendering remains independent.
        page=browser.new_page();page.on('pageerror',lambda e:errors.append(f'older-worker:{e}'));page.set_content(shell());page.evaluate(fake_worker(controller=True,waiting=True));page.add_script_tag(content=JS);page.evaluate("window.dispatchEvent(new CustomEvent('scsi:application-ready',{detail:{version:'3.28.0',state:'ready'}}))");page.wait_for_timeout(80);results['older_worker']=snapshot(page)|{'activation':page.evaluate('window.__activationMessage?.type||""')};page.close()
        # Service workers disabled.
        page=browser.new_page();page.set_content(shell());page.evaluate("Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:undefined})");page.add_script_tag(content=JS);page.evaluate("window.dispatchEvent(new CustomEvent('scsi:application-ready',{detail:{state:'ready'}}))");page.wait_for_timeout(50);results['workers_disabled']=snapshot(page);page.close()
        # Registration failure remains non-blocking.
        page=browser.new_page();page.set_content(shell());page.evaluate(fake_worker(fail=True));page.add_script_tag(content=JS);page.evaluate("window.dispatchEvent(new CustomEvent('scsi:application-ready',{detail:{state:'ready'}}))");page.wait_for_timeout(80);results['registration_failure']=snapshot(page);page.close()
        # Startup exception/no ready event reaches bounded limited mode.
        page=browser.new_page();page.set_content(shell(250));page.evaluate(fake_worker());page.add_script_tag(content=JS);page.wait_for_timeout(360);results['deadline_recovery']=snapshot(page);page.close()
        # Iframe mode posts ready state and reveals its own app.
        page=browser.new_page();page.set_content('<!doctype html><html><body><iframe id="embed"></iframe></body></html>');frame=page.frame_locator('#embed');iframe=page.query_selector('#embed').content_frame();iframe.set_content(shell());iframe.add_script_tag(content=JS);iframe.evaluate("window.dispatchEvent(new CustomEvent('scsi:application-ready',{detail:{state:'ready'}}))");page.wait_for_timeout(80);results['iframe']=snapshot(iframe);page.close();browser.close()
    for key in ('no_existing_worker','older_worker','workers_disabled','registration_failure','iframe'):
        assert results[key]['owner'] and results[key]['ready'] and results[key]['hidden'] and results[key]['startup']=='ready',(key,results[key])
    assert results['older_worker']['activation']=='SC_SI_ACTIVATE_UPDATE',results['older_worker']
    assert results['deadline_recovery']['ready'] and results['deadline_recovery']['hidden'] and results['deadline_recovery']['startup']=='limited',results['deadline_recovery']
    assert not errors,errors
    print(json.dumps(results,indent=2));print('PASS: v3.28.0 single-owner bootstrap and bounded loading recovery passed all startup conditions.');return 0

if __name__=='__main__': raise SystemExit(main())
