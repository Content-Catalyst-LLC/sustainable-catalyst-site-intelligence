#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/coastal-change-v41400.js').read_text()
CSS=(ROOT/'backend/public_app/assets/coastal-change-v41400.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.15.0','contract':'coastal-change-sea-level-blue-carbon',
      'sources':[
        {'id':'noaa-coops','title':'NOAA CO-OPS Tides & Currents','url':'https://tidesandcurrents.noaa.gov/','indicator_types':['observed-water-level','tide-prediction'],'limitations':'Station observations are local and datum-dependent.'},
        {'id':'noaa-digital-coast','title':'NOAA Digital Coast / Sea Level Rise','url':'https://coast.noaa.gov/digitalcoast/','indicator_types':['sea-level-scenario','inundation-screening','tidal-wetland'],'limitations':'Sea-level inundation is screening-level planning information.'},
        {'id':'usgs-coastal-change','title':'USGS Coastal Change Hazards Portal','url':'https://marine.usgs.gov/coastalchangehazardsportal/','indicator_types':['shoreline-change','coastal-erosion-hazard'],'limitations':'Shoreline products carry method and uncertainty limits.'},
        {'id':'global-mangrove-watch','title':'Global Mangrove Watch','url':'https://www.globalmangrovewatch.org/','indicator_types':['mangrove-extent','mangrove-change','blue-carbon-habitat'],'limitations':'Habitat evidence does not establish carbon-credit eligibility.'}],
      'indicator_types':[{'id':'observed-water-level','title':'Observed water level'},{'id':'tide-prediction','title':'Tide prediction'},{'id':'sea-level-scenario','title':'Sea-level scenario'},{'id':'inundation-screening','title':'Inundation screening layer'},{'id':'shoreline-change','title':'Observed shoreline change'},{'id':'coastal-erosion-hazard','title':'Coastal erosion hazard'},{'id':'tidal-wetland','title':'Tidal wetland'},{'id':'mangrove-extent','title':'Mangrove extent'},{'id':'blue-carbon-habitat','title':'Blue-carbon habitat context'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u,'https://gate.local').searchParams,source=qp.get('source')||'noaa-coops',indicator=qp.get('indicator_type')||'observed-water-level',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],a=catalog.indicator_types.find(r=>r.id===indicator)||catalog.indicator_types[0];x={ok:true,version:'4.15.0',contract:'coastal-change-sea-level-blue-carbon',source:s,indicator_type:a,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_indicator_type:(s.indicator_types||[]).includes(a.id),evidence:{water_level_loaded:false,shoreline_record_loaded:false,scenario_layer_loaded:false,habitat_record_loaded:false},truth:{prediction_treated_as_observation:false,scenario_treated_as_exact_flood_forecast:false,shoreline_projection_treated_as_guaranteed_position:false,habitat_treated_as_carbon_stock_estimate:false,habitat_treated_as_carbon_credit:false,platform_safety_finding:false,platform_property_loss_finding:false,platform_regulatory_finding:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="marinePollutionPanel"><div class="mp41300-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSICoastalChangeV41400?.version==='4.15.0'")
    page.locator('#mpCoastalEnter').click(); page.wait_for_function("!document.querySelector('#coastalChangePanel').hidden")
    page.evaluate("""()=>{document.querySelector('#ccSource').value='global-mangrove-watch';document.querySelector('#ccIndicator').value='mangrove-extent';document.querySelector('#ccLat').value='-4.5';document.querySelector('#ccLon').value='39.5'}""")
    page.evaluate("()=>SCSICoastalChangeV41400.refresh()"); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#ccStateTitle')?.textContent.includes('Global Mangrove')")
    m=page.evaluate("""()=>({version:SCSICoastalChangeV41400.version,source:document.querySelector('#ccSource').value,indicator:document.querySelector('#ccIndicator').value,stage:document.querySelector('#ccStageState').textContent,truth:document.querySelector('#ccTruth').textContent,contract:document.querySelector('#coastalChangePanel').dataset.scsiCoastalContract,hidden:document.querySelector('#coastalChangePanel').hidden})""")
    assert m['version']=='4.15.0' and m['source']=='global-mangrove-watch' and m['indicator']=='mangrove-extent'
    assert 'no coastal evidence record loaded' in m['stage'].lower()
    assert 'Scenario = exact flood boundary' in m['truth'] and 'Habitat = carbon stock' in m['truth'] and 'Habitat = carbon credit' in m['truth']
    assert m['contract']=='coastal-change-sea-level-blue-carbon' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2), flush=True); print('PASS: v4.15.0 Coastal Change passed direct and iframe interaction.', flush=True); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
