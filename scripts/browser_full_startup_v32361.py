#!/usr/bin/env python3
"""Complete application-shell Chromium startup validation for v4.15.0.

The managed browser blocks localhost navigation, so this harness loads the production
index HTML and the exact first-party startup assets inline. It exercises the complete
DOM and application bootstrap without contacting external services.
"""
from __future__ import annotations
import json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'backend/public_app'
STARTUP_ASSETS=[
 'assets/vector-cartography-v3230.js','assets/service-recovery-v3224.js','assets/runtime-v3230.js',
 'assets/bootstrap-v32361.js','assets/performance-offline-v3236.js','assets/app.js'
]

def worker_setup(mode:str)->str:
    if mode=='disabled':
        return "(()=>{const bus=new EventTarget();bus.controller=null;bus.register=async()=>{throw new DOMException('Service workers disabled','NotAllowedError')};Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:bus});})();"
    waiting='true' if mode=='older' else 'false'
    controller='{}' if mode in {'older','current'} else 'null'
    fail='throw new Error(\"registration failed\")' if mode=='failure' else 'return registration'
    return f"""(()=>{{const bus=new EventTarget();const waitingWorker={{postMessage:m=>window.__activation=m}};const registration=new EventTarget();registration.waiting={waiting}?waitingWorker:null;registration.installing=null;registration.update=()=>Promise.resolve();bus.controller={controller};bus.register=async()=>{{window.__registerCount=(window.__registerCount||0)+1;{fail}}};Object.defineProperty(navigator,'serviceWorker',{{configurable:true,value:bus}});}})();"""

def document(mode:str,deadline=650)->str:
    html=(APP/'index.html').read_text(encoding='utf-8')
    html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>','',html)
    html=re.sub(r'<script\s+src="[^"]+"\s+defer></script>','',html)
    css='\n'.join(p.read_text(encoding='utf-8') for p in (APP/'assets').glob('*.css'))
    setup=f"""<script>{worker_setup(mode)}(()=>{{const make=()=>{{const data=new Map();return{{getItem:k=>data.has(String(k))?data.get(String(k)):null,setItem:(k,v)=>data.set(String(k),String(v)),removeItem:k=>data.delete(String(k)),clear:()=>data.clear(),key:i=>[...data.keys()][i]||null,get length(){{return data.size}}}}}};try{{Object.defineProperty(window,'localStorage',{{configurable:true,value:make()}});Object.defineProperty(window,'sessionStorage',{{configurable:true,value:make()}})}}catch(_){{}}}})();window.SC_SITE_INTELLIGENCE_API=location.origin;window.fetch=async(input)=>{{const u=String(input);if(u.includes('/public/performance-offline'))return new Response(JSON.stringify({{ok:true,version:'4.15.0',contract:'performance-and-offline-recovery',performance_budgets:{{first_useful_map_ms:3500}}}}),{{status:200,headers:{{'Content-Type':'application/json'}}}});if(u.includes('/public/bootstrap-recovery'))return new Response(JSON.stringify({{ok:true,version:'4.15.0'}}),{{status:200,headers:{{'Content-Type':'application/json'}}}});return new Response(JSON.stringify({{detail:'deterministic startup test: optional service unavailable'}}),{{status:503,headers:{{'Content-Type':'application/json'}}}});}};</script>"""
    scripts='\n'.join(f'<script>{(APP/path).read_text(encoding="utf-8")}</script>' for path in STARTUP_ASSETS)
    html=html.replace('</head>',f'<style>{css}</style>{setup}</head>')
    html=html.replace('data-scsi-startup-deadline-ms="9000"',f'data-scsi-startup-deadline-ms="{deadline}"')
    html=html.replace('</body>',scripts+'</body>')
    return html

def snap(page):
    return page.evaluate("""()=>{const app=document.querySelector('#app'),map=document.querySelector('#map');return{release:app?.dataset.scsiRelease,startup:app?.dataset.startupState||'',ready:app?.classList.contains('app-ready'),launchHidden:document.querySelector('#launchScreen')?.classList.contains('hidden'),owner:Boolean(window.SCSIBootstrapV32361),registrations:window.__registerCount||0,mapWidth:Math.round(map?.getBoundingClientRect().width||0),mapHeight:Math.round(map?.getBoundingClientRect().height||0)}}""")

def main():
    chromium=shutil.which('chromium') or shutil.which('chromium-browser')
    if not chromium:print('SKIP: Chromium unavailable.');return 0
    try:from playwright.sync_api import sync_playwright
    except ImportError:print('SKIP: Playwright unavailable.');return 0
    results={};errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        for mode in ('fresh','current','older','disabled','failure'):
            page=browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e,m=mode:errors.append(f'{m}:{e}'))
            page.set_content(document(mode),wait_until='domcontentloaded',timeout=30000)
            page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=12000)
            page.wait_for_function("document.querySelector('#launchScreen')?.classList.contains('hidden')",timeout=3000)
            results[mode]=snap(page);page.close()
        page=browser.new_page(viewport={'width':1280,'height':900});page.set_content('<iframe id="frame" style="width:1200px;height:820px"></iframe>');frame=page.query_selector('#frame').content_frame();frame.set_content(document('disabled'),wait_until='domcontentloaded');frame.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=12000);frame.wait_for_function("document.querySelector('#launchScreen')?.classList.contains('hidden')",timeout=3000);results['iframe']=snap(frame);page.close();browser.close()
    for key,value in results.items():
        assert value['release']=='4.15.0',(key,value)
        assert value['ready'] and value['launchHidden'] and value['startup'] in {'ready','limited'},(key,value)
        assert value['owner'],(key,value)
        assert value['registrations']<=1,(key,value)
        assert value['mapWidth']>300 and value['mapHeight']>300,(key,value)
    # Optional-service failures are expected warnings; unhandled page errors are not.
    assert not errors,errors
    print(json.dumps(results,indent=2));print('PASS: complete v4.15.0 HTML/app.js startup is visible across worker failure and iframe conditions.');return 0
if __name__=='__main__':raise SystemExit(main())
