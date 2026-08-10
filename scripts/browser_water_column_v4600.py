from pathlib import Path
import json, os, sys, traceback

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT/'backend/public_app/assets/water-column-v4600.js').read_text()
CSS = (ROOT/'backend/public_app/assets/water-column-v4600.css').read_text()


def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None


def fixture_html():
    catalog = {
        'ok': True, 'version': '4.16.0', 'maximum_navigation_depth_m': 11000,
        'sources': [
            {'id':'argo-argovis','title':'Argo profiles via Argovis','url':'https://argo.ucsd.edu/data/','coverage':'global profile coverage','depth_semantics':'source-reported profile samples'},
            {'id':'copernicus-marine','title':'Copernicus Marine 3-D ocean products','url':'https://marine.copernicus.eu/','coverage':'global and regional 3-D products','depth_semantics':'dataset-defined model or analysis depth levels'},
            {'id':'onc-oceans-3','title':'Ocean Networks Canada Oceans 3.0','url':'https://data.oceannetworks.ca/','coverage':'regional observatories; not global','depth_semantics':'instrument/deployment or cast-specific depth'},
        ],
        'variables': [
            {'id':'temperature','title':'Water temperature','short':'TEMP','default_unit':'degC','sources':['argo-argovis','copernicus-marine','onc-oceans-3'],'note':'Evidence classes remain separate.'},
            {'id':'dissolved-oxygen','title':'Dissolved oxygen','short':'O2','default_unit':'umol kg-1','sources':['argo-argovis','copernicus-marine','onc-oceans-3'],'note':'Missing oxygen data is not zero.'},
        ]}
    setup = r'''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams;const variable=qp.get('variable')||'temperature',source=qp.get('source')||'argo-argovis',depth=Number(qp.get('depth_m')||0),v=catalog.variables.find(r=>r.id===variable)||catalog.variables[0],s=catalog.sources.find(r=>r.id===source)||catalog.sources[0];x={ok:true,version:'4.16.0',contract:'water-column-depth-explorer',variable:v,source:s,point:{latitude:Number(qp.get('latitude')||0),longitude:Number(qp.get('longitude')||0)},date:qp.get('date')||null,depth_m:depth,condition:{value:null,record_loaded:false,coverage_verified:false,depth_sample_verified:false},query_plan:{access_kind:source==='copernicus-marine'?'Copernicus Marine 3-D catalogue/subset':'Argovis Argo profile selection'},truth:{value_fabricated:false,depth_value_interpolated:false,nearest_sample_substituted:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__', json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="oceanSurfacePanel"><div class="ocean4500-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''


def exercise(page, label):
    page.set_content(fixture_html(), wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIWaterColumnV4600?.version==='4.16.0'")
    page.locator('#oceanDepthEnter').click()
    page.wait_for_function("!document.querySelector('#waterColumnPanel').hidden")
    page.select_option('#waterVariable','dissolved-oxygen')
    page.select_option('#waterSource','copernicus-marine')
    page.fill('#waterLat','0'); page.fill('#waterLon','-140'); page.fill('#waterDate','2026-08-09')
    page.locator('#waterDepth').fill('1500'); page.locator('#waterDepth').dispatch_event('input')
    page.wait_for_timeout(250)
    page.wait_for_function("document.querySelector('#waterStateTitle')?.textContent.includes('1,500 m')")
    m = page.evaluate("""()=>({version:SCSIWaterColumnV4600.version,variable:document.querySelector('#waterVariable').value,source:document.querySelector('#waterSource').value,depth:document.querySelector('#waterDepth').value,title:document.querySelector('#waterStateTitle').textContent,stage:document.querySelector('#waterStageState').textContent,truth:document.querySelector('#waterTruth').textContent,contract:document.querySelector('#waterColumnPanel').dataset.scsiWaterContract,hidden:document.querySelector('#waterColumnPanel').hidden})""")
    assert m['version']=='4.16.0' and m['variable']=='dissolved-oxygen' and m['source']=='copernicus-marine' and m['depth']=='1500'
    assert 'source sample not loaded' in m['stage'] and 'Not loaded' in m['truth'] and 'None' in m['truth']
    assert m['contract']=='water-column-depth-explorer' and not m['hidden']
    return {'label':label, **m}


def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True, executable_path=path, args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.16.0 Water Column & Depth Explorer passed direct and iframe interaction.'); sys.stdout.flush(); os._exit(0)


if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
