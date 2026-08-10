#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, sys, traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/orbital-earth-v4100.js').read_text(encoding='utf-8').replace('</script','<\\/script')
CSS=(ROOT/'backend/public_app/assets/orbital-earth-v4100.css').read_text(encoding='utf-8')

def find_browser():
    for c in [os.getenv('SC_SI_CHROMIUM',''),shutil.which('chromium') or '',shutil.which('google-chrome') or '',shutil.which('google-chrome-stable') or '', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if c and Path(c).is_file() and os.access(c,os.X_OK): return c
    return None

def page_html():
    payload={
      'ok':True,'version':'4.13.0','contract':'orbital-earth-satellite-observation','mode':'orbital','presentation':'2.5d-orbital-perspective',
      'view':{'center':[0,20],'presentation_altitude_km':1200,'altitude_is_physical_camera_solution':False},
      'observation':{'requested_date':'2026-08-01','layer_id':'true-color','layer_title':'NASA Corrected Reflectance True Color','tile_url':'https://gibs.earthdata.nasa.gov/example/{z}/{y}/{x}.jpg','source':'NASA GIBS','attribution':'NASA EOSDIS GIBS','spatial_resolution':'source and zoom dependent','observation_type':'visible-light satellite mosaic','platform':'Suomi National Polar-orbiting Partnership','instrument':'VIIRS','product_context':'Corrected Reflectance True Color'},
      'footprints':{'instantaneous_sensor_swath':None,'boundary':'Site Intelligence exposes product coverage and selected-view context. It does not invent a pass-specific sensor footprint when no ephemeris/swath source is connected.'},
      'orbit_context':{'real_time_spacecraft_position':None,'ground_track':None,'ephemeris_connected':False,'illustrative_orbit_rings_only':True}
    }
    export={'ok':True,'version':'4.13.0','schema':'sc-site-intelligence-orbital-view/1.0','orbital_state':payload,'review':{'real_satellite_imagery':True,'live_spacecraft_position_claimed':False,'instantaneous_swath_claimed':False,'human_interpretation_required':True},'manifest_sha256':'a'*64}
    setup=f'''<script>
    history.replaceState=()=>{{}};
    window.SC_SITE_INTELLIGENCE_API='https://gate.local';
    const orbital={json.dumps(payload)};const exported={json.dumps(export)};
    window.fetch=async input=>new Response(JSON.stringify(String(input).includes('export-manifest')?exported:orbital),{{status:200,headers:{{'Content-Type':'application/json'}}}});
    (()=>{{let seq=0;window.L={{map:(id,opts)=>{{const o={{_leaflet_id:++seq,_container:document.getElementById(id),_center:{{lat:0,lng:20}},_zoom:2,setView(c,z){{this._center={{lat:Number(c[0]),lng:Number(c[1])}};this._zoom=Number(z);return this}},getCenter(){{return this._center}},getZoom(){{return this._zoom}},setZoom(z){{this._zoom=Number(z);return this}},on(){{return this}},invalidateSize(){{return this}},removeLayer(){{return this}}}};return o}},tileLayer:(url,opts)=>({{url,opts,addTo(map){{this.map=map;return this}},bringToFront(){{return this}}}})}}}})();
    </script>'''
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body>
    <section id="earthStudio" class="earth-studio">
      <select id="earthLayerSelect"><option value="true-color">True color</option></select>
      <input id="earthDateB" value="2026-08-01">
      <button id="earthOrbitEnter" type="button">Enter orbit</button>
      <section id="earthOrbitPanel" class="earth-orbit-panel" hidden aria-busy="false"></section>
    </section>
    <script>{JS}</script></body></html>'''

def exercise(page,label):
    page.wait_for_function("window.SCSIOrbitalEarthV4100?.version==='4.13.0'",timeout=5000)
    page.locator('#earthOrbitEnter').click()
    page.wait_for_function("document.querySelector('#earthStudio').classList.contains('orbit-active')",timeout=5000)
    page.wait_for_function("document.querySelector('#earthOrbitPlatform')?.textContent.includes('VIIRS')",timeout=5000)
    page.locator('[data-orbit-altitude="35786"]').click();page.wait_for_timeout(60)
    m=page.evaluate("""()=>({active:document.querySelector('#earthStudio').classList.contains('orbit-active'),hidden:document.querySelector('#earthOrbitPanel').hidden,altitude:document.querySelector('#earthOrbitAltitude').value,label:document.querySelector('#earthOrbitAltitudeLabel').textContent,platform:document.querySelector('#earthOrbitPlatform').textContent,truth:document.querySelector('#earthOrbitTruth').textContent,center:document.querySelector('#earthOrbitCenter').textContent,map:Boolean(document.querySelector('#earthOrbitMap')),version:window.SCSIOrbitalEarthV4100.version})""")
    page.locator('#earthOrbitReturn').click();page.wait_for_timeout(30);m['surfaceRestored']=page.evaluate("!document.querySelector('#earthStudio').classList.contains('orbit-active') && document.querySelector('#earthOrbitPanel').hidden")
    return {'label':label,'metrics':m}

def main():
    path=find_browser()
    if not path: print('ERROR: Chrome/Chromium required.'); return 2
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start();browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
    html=page_html();results=[];errors=[]
    page=browser.new_page(viewport={'width':1200,'height':850});page.on('pageerror',lambda e:errors.append(f'direct:{e}'));page.set_content(html,wait_until='domcontentloaded');results.append(exercise(page,'direct'))
    outer=browser.new_page(viewport={'width':1200,'height':850});outer.set_content('<iframe id="f" style="width:1100px;height:760px"></iframe>');frame=outer.query_selector('#f').content_frame();frame.set_content(html,wait_until='domcontentloaded');results.append(exercise(frame,'iframe'))
    assert not errors,errors
    for r in results:
        m=r['metrics'];assert m['active'] and not m['hidden'];assert m['altitude']=='35786';assert '35,786' in m['label'];assert 'VIIRS' in m['platform'];assert 'no position fabricated' in m['truth'].lower();assert 'pass-specific sensor footprint' in m['truth'].lower();assert m['map'] and m['version']=='4.13.0' and m['surfaceRestored']
    print(json.dumps({'browser':path,'results':results,'errors':errors},indent=2));print('PASS: v4.13.0 Orbital Earth interaction passed in direct and iframe modes.')
    sys.stdout.flush();sys.stderr.flush();os._exit(0)

if __name__=='__main__':
    try: status=int(main())
    except BaseException: traceback.print_exc();status=1
    sys.stdout.flush();sys.stderr.flush();os._exit(status)
