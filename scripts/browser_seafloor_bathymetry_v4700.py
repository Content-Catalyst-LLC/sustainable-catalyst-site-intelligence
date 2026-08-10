#!/usr/bin/env python3
from pathlib import Path
import json, os, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/seafloor-bathymetry-v4700.js').read_text()
CSS=(ROOT/'backend/public_app/assets/seafloor-bathymetry-v4700.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.14.0','contract':'seafloor-bathymetric-intelligence',
      'sources':[
        {'id':'gebco-2026','title':'GEBCO_2026 global bathymetry','url':'https://www.gebco.net/data-products/gridded-bathymetry-data','coverage':'global ocean-and-land terrain grid','resolution':'15 arc-second global grid','vertical_semantics':'grid elevations are source-product values'},
        {'id':'emodnet-bathymetry','title':'EMODnet Bathymetry','url':'https://emodnet.ec.europa.eu/en/bathymetry','coverage':'European sea regions','resolution':'product-specific','vertical_semantics':'harmonised DTM'},
        {'id':'noaa-ncei-bathymetry','title':'NOAA NCEI Bathymetry & Seafloor Mapping','url':'https://www.ncei.noaa.gov/products/bathymetry','coverage':'survey and DEM holdings','resolution':'survey-specific','vertical_semantics':'survey-specific'},
      ],
      'layers':[
        {'id':'bathymetric-elevation','title':'Bathymetric elevation / depth','short':'DEPTH','sources':['gebco-2026','emodnet-bathymetry','noaa-ncei-bathymetry'],'note':'Sign and datum remain explicit.'},
        {'id':'multibeam-coverage','title':'Multibeam survey coverage','short':'MBES','sources':['noaa-ncei-bathymetry','emodnet-bathymetry'],'note':'Footprint is not sounding density.'},
      ]}
    setup=r'''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,layer=qp.get('layer')||'bathymetric-elevation',source=qp.get('source')||'gebco-2026',l=catalog.layers.find(r=>r.id===layer)||catalog.layers[0],s=catalog.sources.find(r=>r.id===source)||catalog.sources[0];x={ok:true,version:'4.14.0',contract:'seafloor-bathymetric-intelligence',layer:l,source:s,point:{latitude:Number(qp.get('latitude')||0),longitude:Number(qp.get('longitude')||0)},date:qp.get('date')||null,terrain:{value:null,record_loaded:false,point_coverage_verified:false,individual_sounding_verified:false},query_plan:{access_kind:source==='noaa-ncei-bathymetry'?'NOAA NCEI bathymetry survey/catalog discovery':'GEBCO grid / WMS discovery'},truth:{terrain_fabricated:false,grid_spacing_as_accuracy:false,survey_footprint_as_point_measurement:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="waterColumnPanel"><div class="water4600-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSISeafloorV4700?.version==='4.14.0'")
    page.locator('#waterSeafloorEnter').click()
    page.wait_for_function("!document.querySelector('#seafloorPanel').hidden")
    page.select_option('#seaLayer','multibeam-coverage')
    page.select_option('#seaSource','noaa-ncei-bathymetry')
    page.fill('#seaLat','36'); page.fill('#seaLon','-74'); page.fill('#seaDate','2026-08-09')
    page.locator('#seaDate').dispatch_event('change'); page.wait_for_timeout(150)
    page.wait_for_function("document.querySelector('#seaStateTitle')?.textContent.includes('NOAA NCEI')")
    m=page.evaluate("""()=>({version:SCSISeafloorV4700.version,layer:document.querySelector('#seaLayer').value,source:document.querySelector('#seaSource').value,title:document.querySelector('#seaStateTitle').textContent,stage:document.querySelector('#seaStageState').textContent,truth:document.querySelector('#seaTruth').textContent,contract:document.querySelector('#seafloorPanel').dataset.scsiSeafloorContract,hidden:document.querySelector('#seafloorPanel').hidden})""")
    assert m['version']=='4.14.0' and m['layer']=='multibeam-coverage' and m['source']=='noaa-ncei-bathymetry'
    assert 'terrain value not loaded' in m['stage'] and 'Not loaded' in m['truth'] and 'No' in m['truth']
    assert m['contract']=='seafloor-bathymetric-intelligence' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.14.0 Seafloor & Bathymetric Intelligence passed direct and iframe interaction.'); sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
