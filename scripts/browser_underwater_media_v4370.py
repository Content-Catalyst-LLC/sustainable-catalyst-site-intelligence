#!/usr/bin/env python3
"""Browser certification for v4.39.0 live underwater media discovery."""
from __future__ import annotations
import base64, json, os, sys, traceback
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from browser_complete_shell_gate_v32362 import find_browser

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')

PROVIDERS={
  'ok':True,'version':'4.39.0','default_provider':'fathomnet','provider_count':3,
  'providers':[
    {'id':'fathomnet','title':'FathomNet','configured':True,'configuration_required':False,'boundary':'Public source-attributed images and annotations.'},
    {'id':'noaa-ocean-exploration','title':'NOAA Ocean Exploration','configured':True,'configuration_required':False,'boundary':'Public expedition and media discovery.'},
    {'id':'onc-oceans-3','title':'Ocean Networks Canada Oceans 3.0 / SeaTube','configured':False,'configuration_required':True,'boundary':'Token-authenticated archive discovery.'},
  ]
}
SEARCH={
  'ok':True,'version':'4.39.0','contract':'live-underwater-media-discovery-imagery-video-retrieval',
  'query':{'provider':'fathomnet','query':None,'expedition_id':None,'dive_id':None,'location_code':None,'date_from':None,'date_to':None,'latitude':None,'longitude':None,'depth_m':None,'limit':12},
  'record_count':2,
  'results':[
    {'provider':'fathomnet','source_record_id':'fn-live-1','record_type':'underwater-image','title':'Octopus','media_url':'http://127.0.0.1:9998/octopus.jpg','thumbnail_url':'http://127.0.0.1:9998/octopus.jpg','source_record_url':'https://database.fathomnet.org/','latitude':36.8,'longitude':-122.0,'depth_m':812.5,'observed_at':'2026-01-02T03:04:05Z','annotations':['Octopus'],'credit':'FathomNet contributor','rights':'Verify asset-specific rights.'},
    {'provider':'fathomnet','source_record_id':'fn-live-2','record_type':'underwater-image','title':'Deep-sea coral','media_url':'http://127.0.0.1:9998/coral.jpg','thumbnail_url':'http://127.0.0.1:9998/coral.jpg','source_record_url':'https://database.fathomnet.org/','latitude':None,'longitude':None,'depth_m':None,'observed_at':None,'annotations':['Coral'],'credit':'FathomNet contributor','rights':'Verify asset-specific rights.'},
  ],
  'provider_states':{'fathomnet':{'ok':True,'record_count':2,'mode':'LIVE','network_calls_performed':True}},
  'truth':{'visual_media_fabricated':False,'missing_media_replaced':False,'provider_failure_blocks_other_providers':False,'onc_token_exposed':False,'annotation_promoted_to_population_claim':False,'point_depth_time_match_inferred':False}
}


def main()->int:
    browser_path=find_browser()
    if not browser_path:
        print('ERROR: Chromium or Chrome is required for v4.39.0 underwater browser certification.'); return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('ERROR: Playwright is required for v4.39.0 underwater browser certification.'); return 2
    js=(ROOT/'backend/public_app/assets/underwater-observation-v4800.js').read_text(encoding='utf-8')
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1050})
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route_handler(route):
            u=urlsplit(route.request.url)
            if u.netloc=='127.0.0.1:9998' and u.path=='/app/':
                route.fulfill(status=200,content_type='text/html',body='<!doctype html><html><head></head><body><section id="seafloorPanel"><div class="sea4700-actions"></div></section></body></html>'); return
            if u.netloc=='127.0.0.1:9998' and u.path.endswith('/underwater-observation-v4800.css'):
                route.fulfill(status=200,content_type='text/css',body=''); return
            if u.netloc=='127.0.0.1:9998' and u.path=='/public/underwater-media/providers':
                route.fulfill(status=200,content_type='application/json',body=json.dumps(PROVIDERS)); return
            if u.netloc=='127.0.0.1:9998' and u.path=='/public/underwater-media/search':
                request=json.loads(route.request.post_data or '{}')
                payload=json.loads(json.dumps(SEARCH))
                payload['query'].update({k:request.get(k) for k in payload['query'] if k in request})
                route.fulfill(status=200,content_type='application/json',body=json.dumps(payload)); return
            if u.netloc=='127.0.0.1:9998' and u.path.endswith(('.jpg','.png')):
                route.fulfill(status=200,content_type='image/png',body=PNG); return
            route.abort()
        page.route('**/*',route_handler)
        page.set_content("""<!doctype html><html><head></head><body><section id="seafloorPanel"><div class="sea4700-actions"></div></section><script>
window.SC_SITE_INTELLIGENCE_API='http://127.0.0.1:9998';
history.replaceState=()=>{};
const NativeURL=window.URL;
function HarnessURL(value,base){ return new NativeURL(value, base==='null' ? 'https://harness.invalid/' : base); }
HarnessURL.createObjectURL=NativeURL.createObjectURL?.bind(NativeURL);
HarnessURL.revokeObjectURL=NativeURL.revokeObjectURL?.bind(NativeURL);
window.URL=HarnessURL;
</script></body></html>""",wait_until='domcontentloaded')
        page.add_script_tag(content=js)
        page.wait_for_function('window.SCSIUnderwaterV4800?.version === "4.39.0"',timeout=5000)
        page.evaluate('()=>window.SCSIUnderwaterV4800.enter()')
        page.wait_for_function('document.querySelectorAll("#uwResults [data-index]").length === 2',timeout=10000)
        page.wait_for_function('document.querySelector("#uwImage") && !document.querySelector("#uwImage").hidden',timeout=5000)
        state=page.evaluate('''()=>({
          visible:!document.querySelector('#underwaterObservationPanel')?.hidden,
          provider:document.querySelector('#uwSource')?.value,
          providers:[...document.querySelectorAll('#uwSource option')].map(x=>x.value),
          cards:document.querySelectorAll('#uwResults [data-index]').length,
          image:document.querySelector('#uwImage')?.src||'',
          title:document.querySelector('#uwStageTitle')?.textContent||'',
          depth:document.querySelector('#uwDepth')?.value,
          lat:document.querySelector('#uwLat')?.value,
          lon:document.querySelector('#uwLon')?.value,
          truth:document.querySelector('#uwTruth')?.textContent||'',
          tokenWarning:document.querySelector('#uwSource option[value="onc-oceans-3"]')?.textContent||''
        })''')
        assert state['visible'] is True and state['provider']=='fathomnet',state
        assert state['providers']==['fathomnet','noaa-ocean-exploration','onc-oceans-3'],state
        assert state['cards']==2 and state['title']=='Octopus',state
        assert state['image'].startswith('http://127.0.0.1:9998/octopus.jpg'),state
        assert state['depth']=='' and state['lat']=='' and state['lon']=='',state
        assert 'No' in state['truth'] and 'token required' in state['tokenWarning'],state
        browser.close()
    assert not errors,errors
    print(json.dumps({'browser':browser_path,'state':state,'errors':errors},indent=2))
    print('PASS: v4.39.0 renders live underwater candidate media, defaults to FathomNet, keeps ONC optional, and does not fabricate 0,0/depth defaults.')
    return 0

if __name__=='__main__':
    try: status=int(main())
    except BaseException:
        traceback.print_exc(); status=1
    try: sys.stdout.flush(); sys.stderr.flush()
    finally: os._exit(status)
