from pathlib import Path
import json, os, sys, traceback

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/ocean-surface-v4500.js').read_text()
CSS=(ROOT/'backend/public_app/assets/ocean-surface-v4500.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.16.0',
      'sources':[
        {'id':'noaa-coastwatch-erddap','title':'NOAA CoastWatch / OceanWatch ERDDAP','url':'https://coastwatch.noaa.gov/erddap/','coverage':'global and regional satellite ocean products'},
        {'id':'ioos-catalog','title':'U.S. IOOS Data Catalog','url':'https://data.ioos.us/','coverage':'United States coastal and regional systems; not global'},
        {'id':'copernicus-marine','title':'Copernicus Marine Service','url':'https://marine.copernicus.eu/','coverage':'global and regional ocean products'},
      ],
      'variables':[
        {'id':'sea-surface-temperature','title':'Sea-surface temperature','short':'SST','default_unit':'degC','sources':['noaa-coastwatch-erddap','copernicus-marine','ioos-catalog'],'evidence_note':'Evidence classes remain separate.'},
        {'id':'surface-currents','title':'Surface currents','short':'CURRENT','default_unit':'m s-1','sources':['noaa-coastwatch-erddap','copernicus-marine','ioos-catalog'],'evidence_note':'Observed, blended, analyzed, and forecast currents remain distinct.'},
      ]}
    setup=r'''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const q=new URL(u).searchParams;const variable=q.get('variable')||'sea-surface-temperature',source=q.get('source')||'noaa-coastwatch-erddap',v=catalog.variables.find(r=>r.id===variable)||catalog.variables[0],s=catalog.sources.find(r=>r.id===source)||catalog.sources[0];x={ok:true,version:'4.16.0',variable:v,source:s,point:{latitude:Number(q.get('latitude')||0),longitude:Number(q.get('longitude')||0)},date:q.get('date')||null,condition:{value:null,record_loaded:false,current_condition_claimed:false,coverage_verified:false},query_plan:{access_kind:source==='copernicus-marine'?'Copernicus Marine Toolbox catalogue/subset':'ERDDAP dataset discovery / subset'},truth:{value_fabricated:false,missing_replaced:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="earthStudio"><div class="earth-studio-actions"><button id="earthOrbitEnter">Enter orbit</button></div><section id="earthOrbitPanel"></section></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIOceanSurfaceV4500?.version==='4.16.0'")
    page.locator('#earthOceanEnter').click()
    page.wait_for_function("!document.querySelector('#oceanSurfacePanel').hidden")
    page.select_option('#oceanVariable','surface-currents')
    page.select_option('#oceanSource','copernicus-marine')
    page.fill('#oceanLat','0'); page.fill('#oceanLon','-140'); page.fill('#oceanDate','2026-08-09'); page.locator('#oceanDate').dispatch_event('change')
    page.wait_for_function("document.querySelector('#oceanStateTitle')?.textContent.includes('Copernicus')")
    m=page.evaluate("""()=>({version:SCSIOceanSurfaceV4500.version,variable:document.querySelector('#oceanVariable').value,source:document.querySelector('#oceanSource').value,title:document.querySelector('#oceanStateTitle').textContent,stage:document.querySelector('#oceanStageState').textContent,truth:document.querySelector('#oceanTruth').textContent,contract:document.querySelector('#oceanSurfacePanel').dataset.scsiOceanContract,hidden:document.querySelector('#oceanSurfacePanel').hidden})""")
    assert m['version']=='4.16.0' and m['variable']=='surface-currents' and m['source']=='copernicus-marine'
    assert 'value not loaded' in m['stage'] and 'Not loaded' in m['truth'] and 'Not verified' in m['truth']
    assert m['contract']=='global-ocean-intelligence-surface-conditions' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':850}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':850}); outer.set_content('<iframe id="f" style="width:1100px;height:760px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.16.0 Global Ocean Intelligence passed direct and iframe interaction.'); sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
