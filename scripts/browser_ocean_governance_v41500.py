#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/ocean-governance-v41500.js').read_text()
CSS=(ROOT/'backend/public_app/assets/ocean-governance-v41500.css').read_text()
def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
def fixture_html():
    catalog={'ok':True,'version':'4.17.0','contract':'ocean-governance-jurisdiction-maritime-boundaries','sources':[{'id':'noaa-maritime-boundaries','title':'NOAA U.S. Maritime Limits & Boundaries','zone_types':['territorial-sea','contiguous-zone','exclusive-economic-zone'],'limitations':'Orientation only.'},{'id':'marine-regions-vliz','title':'Marine Regions Maritime Boundaries','zone_types':['territorial-sea','exclusive-economic-zone','high-seas'],'limitations':'Compiled geometry is not a platform legal opinion.'},{'id':'fao-major-fishing-areas','title':'FAO Major Fishing Areas','zone_types':['fao-major-fishing-area'],'limitations':'Statistical areas are not jurisdiction.'},{'id':'fao-regional-fishery-bodies','title':'FAO Regional Fishery Bodies','zone_types':['regional-fishery-body-area'],'limitations':'RFB coverage is management context.'}], 'zone_types':[{'id':'territorial-sea','title':'Territorial sea'},{'id':'exclusive-economic-zone','title':'Exclusive economic zone'},{'id':'high-seas','title':'High seas'},{'id':'fao-major-fishing-area','title':'FAO Major Fishing Area'},{'id':'regional-fishery-body-area','title':'Regional Fishery Body area'}]}
    setup="""<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u,'https://gate.local').searchParams,source=qp.get('source')||'marine-regions-vliz',zone=qp.get('zone_type')||'exclusive-economic-zone',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],z=catalog.zone_types.find(r=>r.id===zone)||catalog.zone_types[0];x={ok:true,version:'4.17.0',contract:'ocean-governance-jurisdiction-maritime-boundaries',source:s,zone_type:z,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_zone_type:(s.zone_types||[]).includes(z.id),evidence:{zone_record_loaded:false,management_area_loaded:false,treaty_metadata_loaded:false},truth:{platform_legal_boundary_determination:false,platform_sovereignty_determination:false,statistical_area_treated_as_jurisdiction:false,rfb_area_treated_as_sovereignty:false,fishing_authorization_inferred:false,enforcement_finding:false,navigation_authority:false,dispute_resolved_by_platform:false}}}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>""".replace('__CATALOG__',json.dumps(catalog))
    return f'<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="coastalChangePanel"><div class="cc41400-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'
def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIOceanGovernanceV41500?.version==='4.17.0'")
    page.locator('#ccGovernanceEnter').click(); page.wait_for_function("!document.querySelector('#oceanGovernancePanel').hidden")
    page.evaluate("()=>{document.querySelector('#ogSource').value='fao-major-fishing-areas';document.querySelector('#ogZone').value='fao-major-fishing-area';document.querySelector('#ogLat').value='40';document.querySelector('#ogLon').value='-50'}")
    page.evaluate("()=>SCSIOceanGovernanceV41500.refresh()"); page.wait_for_timeout(100)
    page.wait_for_function("document.querySelector('#ogStageState')?.textContent.includes('FAO Major')")
    m=page.evaluate("()=>({version:SCSIOceanGovernanceV41500.version,source:document.querySelector('#ogSource').value,zone:document.querySelector('#ogZone').value,stage:document.querySelector('#ogStageState').textContent,truth:document.querySelector('#ogTruth').textContent,contract:document.querySelector('#oceanGovernancePanel').dataset.scsiOceanGovernanceContract,hidden:document.querySelector('#oceanGovernancePanel').hidden})")
    assert m['version']=='4.17.0' and m['source']=='fao-major-fishing-areas' and m['zone']=='fao-major-fishing-area'
    assert 'no governance evidence record loaded' in m['stage'].lower()
    assert 'Geometry = legal determination' in m['truth'] and 'Statistical area = jurisdiction' in m['truth'] and 'RFB area = sovereignty' in m['truth']
    assert m['contract']=='ocean-governance-jurisdiction-maritime-boundaries' and not m['hidden']
    return {'label':label,**m}
def main():
    path=browser_path()
    if not path: print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    r1=exercise(browser.new_page(viewport={'width':1200,'height':900}),'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); r2=exercise(outer.query_selector('#f').content_frame(),'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2),flush=True); print('PASS: v4.17.0 Ocean Governance passed direct and iframe interaction.',flush=True); os._exit(0)
if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
