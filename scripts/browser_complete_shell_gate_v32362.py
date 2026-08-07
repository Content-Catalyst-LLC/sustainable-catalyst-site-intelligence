#!/usr/bin/env python3
"""Mandatory complete production-shell browser gate for Site Intelligence v3.28.0.

The harness uses the exact shipped index HTML and every first-party script in document
order. It runs in-memory because some managed validation environments administratively
block localhost navigation. On a developer Mac it still exercises the same production
DOM, CSS, JavaScript, service-worker ownership, route modules, and accessibility runtime.
"""
from __future__ import annotations

import traceback

import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'backend/public_app'
VERSION='3.28.0'

def find_browser():
    candidates=[
      os.getenv('SC_SI_CHROMIUM',''),
      shutil.which('chromium') or '',shutil.which('chromium-browser') or '',
      shutil.which('google-chrome') or '',shutil.which('google-chrome-stable') or '',
      shutil.which('microsoft-edge') or '',shutil.which('brave-browser') or '',
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
      str(Path.home()/'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
      str(Path.home()/'Applications/Chromium.app/Contents/MacOS/Chromium'),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate,os.X_OK):return candidate
    return None

def endpoint_payloads():
    sys.path.insert(0,str(ROOT/'backend'))
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    paths=['/public/browser-reliability','/public/performance-offline','/public/bootstrap-recovery','/public/mutation-observer-recovery','/public/startup-stability','/public/data-truth','/public/data-truth/countries','/public/data-truth/country/KEN','/public/data-truth/country/BRA','/public/countries','/public/countries/regions','/public/workspaces/production-truth','/public/maps/interaction','/public/workflows/analytical','/public/runtime-health','/public/record-truth/indicator/KEN/SP.POP.TOTL','/public/record-truth/map-layer/true-color','/public/record-truth/manifest','/public/data-truth/control-plane','/public/data-truth/control-plane/schema-drift','/public/data-truth/control-plane/outages','/public/data-truth/control-plane/coverage?countries=KEN,BRA,USA','/public/data-truth/control-plane/workspaces?country=KEN','/public/data-truth/control-plane/export?country=KEN','/public/assurance','/public/assurance/model-cards','/public/research-integration','/public/monitoring-operations']
    payloads={path:client.get(path).json() for path in paths}
    for path, payload in list(payloads.items()):
        payloads.setdefault(path.split('?', 1)[0], payload)
    payloads['/public/record-truth/resolve']=client.post('/public/record-truth/resolve',json={'record_type':'event','id':'browser-gate-event','title':'Browser gate event','source':'USGS','source_url':'https://earthquake.usgs.gov/','observed_at':'2026-08-05T00:00:00Z','country_code':'USA','data_state':'live'}).json()
    return payloads

def worker_setup(mode):
    if mode=='disabled':
        return "(()=>{const bus=new EventTarget();bus.controller=null;bus.register=async()=>{throw new DOMException('Service workers disabled','NotAllowedError')};Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:bus});})();"
    fail="throw new Error('registration failed')" if mode=='failure' else 'return registration'
    return f"""(()=>{{const bus=new EventTarget();bus.controller=null;const registration=new EventTarget();registration.waiting=null;registration.installing=null;registration.update=()=>Promise.resolve();bus.register=async()=>{{window.__registerCount=(window.__registerCount||0)+1;{fail}}};Object.defineProperty(navigator,'serviceWorker',{{configurable:true,value:bus}});}})();"""

def document(mode='disabled'):
    html=(APP/'index.html').read_text(encoding='utf-8')
    script_paths=re.findall(r'<script\s+src="([^"]+)"\s+defer></script>',html)
    if len(script_paths)<30:raise RuntimeError(f'Expected complete script chain; found {len(script_paths)} scripts.')
    html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>','',html)
    html=re.sub(r'<script\s+src="[^"]+"\s+defer></script>','',html)
    css='\n'.join(p.read_text(encoding='utf-8') for p in sorted((APP/'assets').glob('*.css')))
    payloads=json.dumps(endpoint_payloads(),separators=(',',':'))
    setup=f"""<script>{worker_setup(mode)}
    (()=>{{const make=()=>{{const data=new Map();return{{getItem:k=>data.has(String(k))?data.get(String(k)):null,setItem:(k,v)=>data.set(String(k),String(v)),removeItem:k=>data.delete(String(k)),clear:()=>data.clear(),key:i=>[...data.keys()][i]||null,get length(){{return data.size}}}}}};try{{Object.defineProperty(window,'localStorage',{{configurable:true,value:make()}});Object.defineProperty(window,'sessionStorage',{{configurable:true,value:make()}})}}catch(_){{}}}})();
    try{{history.replaceState=()=>{{}};history.pushState=()=>{{}}}}catch(_){{}};const NativeRequest=window.Request;window.Request=function(input,init){{if(typeof input==='string')input=new URL(input,'https://gate.local').href;return new NativeRequest(input,init)}};window.Request.prototype=NativeRequest.prototype;window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.__expectedScriptCount={len(script_paths)};window.__executedScripts=[];
    const payloads={payloads};window.fetch=async(input)=>{{const raw=String(input);let path='';try{{path=new URL(raw,location.href).pathname}}catch(_){{path=raw.split('?')[0]}};if(payloads[path])return new Response(JSON.stringify(payloads[path]),{{status:200,headers:{{'Content-Type':'application/json'}}}});if(path.endsWith('.geojson'))return new Response(JSON.stringify({{type:'FeatureCollection',features:[]}}),{{status:200,headers:{{'Content-Type':'application/geo+json'}}}});return new Response(JSON.stringify({{detail:'complete-shell deterministic gate: optional service unavailable'}}),{{status:503,headers:{{'Content-Type':'application/json'}}}});}};
    </script>"""
    blocks=[]
    for path in script_paths:
        local=APP/path.split('?',1)[0].removeprefix('/app/')
        text=local.read_text(encoding='utf-8').replace('</script','<\\/script')
        blocks.append(f'<script>window.__executedScripts.push({json.dumps(path)});\n{text}</script>')
    html=html.replace('</head>',f'<style>{css}</style>{setup}</head>')
    html=html.replace('</body>','\n'.join(blocks)+'</body>')
    return html,len(script_paths)

def snapshot(page):
    return page.evaluate("""()=>{const app=document.querySelector('#app'),map=document.querySelector('#map'),r=window.SCSIBrowserReliabilityV3235?.getState?.()||{};return{release:app?.dataset.scsiRelease||'',startup:app?.dataset.startupState||'',ready:Boolean(app?.classList.contains('app-ready')),launchHidden:Boolean(document.querySelector('#launchScreen')?.classList.contains('hidden')),mapWidth:Math.round(map?.getBoundingClientRect().width||0),mapHeight:Math.round(map?.getBoundingClientRect().height||0),reliabilityReady:Boolean(window.SCSIBrowserReliabilityV3235),dataTruthReady:Boolean(window.SCSIDataTruthV32371),productionTruthReady:Boolean(window.SCSIProductionTruthV3231),recordTruthReady:Boolean(window.SCSIRecordProvenanceV3238),controlPlaneReady:Boolean(window.SCSIDataTruthControlPlaneV3240),researchIntegrationReady:Boolean(window.SCSIResearchIntegrationV3270),monitoringOperationsReady:Boolean(window.SCSIMonitoringOperationsV3280),bootstrapReady:Boolean(window.SCSIBootstrapV32361),summaryPasses:Number(r.summaryPasses||0),summaryWrites:Number(r.summaryWrites||0),summarySuppressed:Number(r.summarySuppressed||0),summaryCount:document.querySelectorAll('.scsi-map-summary').length,countryOptionCount:document.querySelectorAll('#countrySelect option').length,countryValue:document.querySelector('#countrySelect')?.value||'',executedScripts:(window.__executedScripts||[]).length,expectedScripts:Number(window.__expectedScriptCount||0)}}""")

def assert_ready(label,result):
    assert result['release']==VERSION,(label,result)
    assert result['ready'] and result['launchHidden'],(label,result)
    assert result['startup'] in {'ready','limited'},(label,result)
    assert result['mapWidth']>300 and result['mapHeight']>300,(label,result)
    assert result['reliabilityReady'] and result['dataTruthReady'] and result['recordTruthReady'] and result['controlPlaneReady'] and result['researchIntegrationReady'] and result['monitoringOperationsReady'] and result['productionTruthReady'] and result['bootstrapReady'],(label,result)
    assert result['summaryCount']>=1,(label,result)
    assert result['countryOptionCount']>=170,(label,result)
    assert result['countryValue']=='KEN',(label,result)
    assert result['executedScripts']==result['expectedScripts'] and result['expectedScripts']>=30,(label,result)

def main():
    browser_path=find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for the complete-shell browser gate.',file=sys.stderr);return 2
    try:from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for the complete-shell browser gate.',file=sys.stderr);return 2
    results={};errors=[];console=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        for mode in ('disabled','failure'):
            html,script_count=document(mode)
            page=browser.new_page(viewport={'width':1280,'height':900});page.on('pageerror',lambda e,m=mode:errors.append(f'{m}:{e}'));page.on('console',lambda msg,m=mode:console.append(f'{m}:{msg.text}') if msg.type=='error' else None)
            page.set_content(html,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
            page.wait_for_function("window.SCSIDataTruthV32371 && window.SCSIRecordProvenanceV3238 && window.SCSIDataTruthControlPlaneV3240 && window.SCSIResearchIntegrationV3270 && window.SCSIMonitoringOperationsV3280 && window.SCSIProductionTruthV3231",timeout=12000)
            page.wait_for_timeout(500)
            before=snapshot(page)
            page.evaluate("""()=>{const map=document.querySelector('#map');for(let i=0;i<80;i++){const n=document.createElement('i');n.className='observer-gate-probe';map.append(n);n.remove()}}""")
            page.wait_for_timeout(300)
            after=snapshot(page);assert_ready(mode,after)
            assert after['summaryPasses']-before['summaryPasses']<=4,(before,after)
            assert after['summaryWrites']-before['summaryWrites']<=2,(before,after)
            assert page.evaluate("document.querySelector('#app').classList.contains('app-ready')") is True
            results[mode]={'before':before,'after':after,'scriptCount':script_count};page.close()
        # iframe document, exact same complete shell.
        outer=browser.new_page(viewport={'width':1280,'height':920});outer.set_content('<iframe id="gate" style="width:1180px;height:820px;border:0"></iframe>');frame=outer.query_selector('#gate').content_frame();html,script_count=document('disabled');frame.set_content(html,wait_until='domcontentloaded',timeout=45000)
        frame.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000);frame.wait_for_function("window.SCSIDataTruthV32371 && window.SCSIRecordProvenanceV3238 && window.SCSIDataTruthControlPlaneV3240 && window.SCSIResearchIntegrationV3270 && window.SCSIMonitoringOperationsV3280 && window.SCSIProductionTruthV3231",timeout=12000);frame.wait_for_timeout(500);results['iframe']=snapshot(frame);assert_ready('iframe',results['iframe']);outer.close();browser.close()
    assert not errors,errors
    actionable=[item for item in console if not any(token in item.lower() for token in ('failed to load resource','net::err_','favicon'))]
    assert not actionable,actionable
    print(json.dumps({'browser':browser_path,'results':results,'filteredConsoleErrors':console},indent=2))
    print('PASS: complete v3.28.0 production shell is responsive, observer-bounded, and fully initialized in direct and iframe modes.')
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
