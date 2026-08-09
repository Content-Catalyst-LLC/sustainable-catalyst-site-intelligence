#!/usr/bin/env python3
from pathlib import Path
import json, os, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/underwater-observation-v4800.js').read_text()
CSS=(ROOT/'backend/public_app/assets/underwater-observation-v4800.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.8.0','contract':'underwater-observation-visual-evidence',
      'sources':[
        {'id':'onc-oceans-3','title':'Ocean Networks Canada Oceans 3.0 / SeaTube','url':'https://data.oceannetworks.ca/','coverage':'observatory media','limitations':'Coverage is deployment-specific.'},
        {'id':'fathomnet','title':'FathomNet underwater imagery and annotations','url':'https://www.fathomnet.org/','coverage':'contributor imagery','limitations':'Annotations remain source-specific evidence.'},
        {'id':'noaa-ocean-exploration','title':'NOAA Ocean Exploration expedition media','url':'https://oceanexplorer.noaa.gov/data/access/','coverage':'expedition media','limitations':'Dive presence does not prove point media coverage.'},
      ],
      'media_types':[
        {'id':'still-image','title':'Underwater still image'},
        {'id':'video-segment','title':'Underwater video segment'},
        {'id':'video-stream','title':'Underwater video stream / archive stream'},
        {'id':'live-camera-reference','title':'Live-camera reference'},
      ]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'onc-oceans-3',media=qp.get('media_type')||'still-image',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],m=catalog.media_types.find(r=>r.id===media)||catalog.media_types[0];x={ok:true,version:'4.8.0',contract:'underwater-observation-visual-evidence',source:s,media_type:m,point:{latitude:Number(qp.get('latitude')||0),longitude:Number(qp.get('longitude')||0)},depth_m:Number(qp.get('depth_m')||0),date:qp.get('date')||null,query:qp.get('query')||null,media:{record_loaded:false,media_url:null,location_verified:false,depth_verified:false,rights_verified:false},annotation:{record_loaded:false},environmental_context:{records_loaded:false,co_temporal_verified:false,co_located_verified:false},query_plan:{access_kind:source==='fathomnet'?'FathomNet image / concept / annotation discovery':'source discovery'},truth:{visual_media_fabricated:false,catalog_entry_as_point_coverage:false,annotation_as_taxonomic_verification:false,model_inference_as_verified_observation:false,sensor_context_assumed_cotemporal:false,sensor_context_assumed_colocated:false,reuse_rights_inferred:false,missing_media_replaced:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="seafloorPanel"><div class="sea4700-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIUnderwaterV4800?.version==='4.8.0'")
    page.locator('#seaUnderwaterEnter').click()
    page.wait_for_function("!document.querySelector('#underwaterObservationPanel').hidden")
    page.select_option('#uwSource','fathomnet'); page.select_option('#uwMedia','still-image')
    page.fill('#uwDepth','1200'); page.fill('#uwLat','36.7'); page.fill('#uwLon','-122'); page.fill('#uwQuery','Octopus')
    page.locator('#uwQuery').dispatch_event('change'); page.wait_for_timeout(150)
    page.wait_for_function("document.querySelector('#uwStateTitle')?.textContent.includes('FathomNet')")
    m=page.evaluate("""()=>({version:SCSIUnderwaterV4800.version,source:document.querySelector('#uwSource').value,media:document.querySelector('#uwMedia').value,stage:document.querySelector('#uwStageState').textContent,truth:document.querySelector('#uwTruth').textContent,contract:document.querySelector('#underwaterObservationPanel').dataset.scsiUnderwaterContract,hidden:document.querySelector('#underwaterObservationPanel').hidden,depth:document.querySelector('#uwDepth').value,query:document.querySelector('#uwQuery').value})""")
    assert m['version']=='4.8.0' and m['source']=='fathomnet' and m['media']=='still-image'
    assert m['depth']=='1200' and m['query']=='Octopus'
    assert 'media not loaded' in m['stage'].lower() and 'Not loaded' in m['truth'] and 'No' in m['truth']
    assert m['contract']=='underwater-observation-visual-evidence' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.8.0 Underwater Observation & Visual Evidence passed direct and iframe interaction.'); sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
