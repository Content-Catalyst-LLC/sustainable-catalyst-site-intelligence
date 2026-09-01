#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, traceback
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from browser_complete_shell_gate_v32362 import find_browser
PROVIDERS={'ok':True,'version':'4.39.1','provider_count':5,'default_provider':'astronomy-observations','providers':[{'id':'planetary-imagery','title':'Planetary imagery','organization':'USGS Astrogeology'},{'id':'astronomy-observations','title':'Astronomical observations','organization':'MAST / STScI'},{'id':'solar-system-ephemeris','title':'Solar-system ephemeris','organization':'NASA JPL'},{'id':'exoplanets','title':'Exoplanets','organization':'NASA Exoplanet Archive'},{'id':'seti-archive','title':'SETI archive discovery','organization':'Breakthrough Listen'}]}
SEARCH={'ok':True,'version':'4.39.1','provider':'astronomy-observations','state':'ready','result_count':2,'results':[{'provider':'astronomy-observations','record_type':'mast-observation','source_record_id':'123','title':'M31','source_record_url':'https://mast.stsci.edu/','observed_at':'59000','metadata':{'mission':'HST','instrument':'ACS'},'truth':'Archive observation metadata is not a live telescope image.'},{'provider':'astronomy-observations','record_type':'mast-observation','source_record_id':'124','title':'M31 field','source_record_url':'https://mast.stsci.edu/','metadata':{'mission':'JWST','instrument':'NIRCam'},'truth':'Archive observation metadata is not a live telescope image.'}]}

def main():
    bp=find_browser()
    if not bp: print('ERROR: Chrome/Chromium required');return 2
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=bp,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        p=b.new_page(viewport={'width':1024,'height':900});p.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            u=urlsplit(r.request.url)
            if u.netloc=='127.0.0.1:9998' and u.path=='/public/space-observation/providers':r.fulfill(status=200,content_type='application/json',body=json.dumps(PROVIDERS));return
            if u.netloc=='127.0.0.1:9998' and u.path=='/public/space-observation/search':r.fulfill(status=200,content_type='application/json',body=json.dumps(SEARCH));return
            r.abort()
        p.route('**/*',route)
        app=(ROOT/'backend/public_app/assets/app.css').read_text();unified=(ROOT/'backend/public_app/assets/unified-platform-v4000.css').read_text();iframe=(ROOT/'backend/public_app/assets/iframe-navigation-v4380.css').read_text();spacecss=(ROOT/'backend/public_app/assets/live-space-observation-v4380.css').read_text();spacejs=(ROOT/'backend/public_app/assets/live-space-observation-v4380.js').read_text()
        p.set_content(f'''<!doctype html><html class="scsi-wordpress-fixed-embed"><head><style>{app}\n{unified}\n{iframe}\n{spacecss}</style></head><body><div class="app-shell"><header class="topbar"></header><aside class="sidebar"><nav class="v4000-nav-featured"><button class="nav-item" data-ocean-entry="hub"><span>Ocean</span><small>Observation and marine systems</small></button><button class="nav-item" data-space-entry="hub"><span>Space</span><small>Orbital, planetary, astronomy &amp; SETI</small></button></nav></aside><main class="workspace"><section id="liveSpaceObservation" class="space4380-panel" hidden></section></main></div><script>window.SC_SITE_INTELLIGENCE_API='http://127.0.0.1:9998';window.__modules=[];window.SCScienceV240={{openLocalWorkspace:(x)=>window.__modules.push(x)}};</script></body></html>''')
        p.add_script_tag(content=spacejs);p.wait_for_function('window.SCSILiveSpaceV4380?.version === "4.39.1"')
        p.evaluate('()=>window.SCSILiveSpaceV4380.enter()');p.wait_for_function('document.querySelectorAll("#space4380Results [data-space-record]").length===2')
        widths=[]
        for width in (1024,900,768):
            p.set_viewport_size({'width':width,'height':900});p.wait_for_timeout(60)
            widths.append(p.evaluate('''()=>({viewport:innerWidth,sidebar:document.querySelector('.sidebar').getBoundingClientRect().width,spaceFont:parseFloat(getComputedStyle(document.querySelector('[data-space-entry] span')).fontSize),spaceText:document.querySelector('[data-space-entry]').innerText,overflow:document.querySelector('[data-space-entry]').scrollWidth>document.querySelector('[data-space-entry]').clientWidth+2})'''))
        for x in widths:
            assert x['sidebar']>=210,x
            assert x['spaceFont']>=12,x
            assert 'Space' in x['spaceText'] and 'Orbital' in x['spaceText'],x
            assert x['overflow'] is False,x
        result=p.evaluate('''()=>({visible:!document.querySelector('#liveSpaceObservation').hidden,provider:document.querySelector('#space4380Provider').value,count:document.querySelectorAll('#space4380Results [data-space-record]').length,modules:document.querySelectorAll('[data-space-module]').length,status:document.querySelector('#space4380Status').textContent})''')
        assert result['visible'] and result['provider']=='astronomy-observations' and result['count']==2 and result['modules']==6,result
        b.close()
    assert not errors,errors
    print(json.dumps({'browser':bp,'iframe_widths':widths,'space':result,'errors':errors},indent=2))
    print('PASS: v4.39.1 renders live Space archive results and preserves readable Ocean/Space text controls across desktop iframe widths.')
    return 0
if __name__=='__main__':
    try:status=int(main())
    except BaseException:traceback.print_exc();status=1
    try:sys.stdout.flush();sys.stderr.flush()
    finally:os._exit(status)
