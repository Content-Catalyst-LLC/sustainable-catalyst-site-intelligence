#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/ocean-events-v41100.js').read_text()
CSS=(ROOT/'backend/public_app/assets/ocean-events-v41100.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.17.0','contract':'ocean-events-hazards-ecosystem-change',
      'sources':[
        {'id':'noaa-coral-reef-watch','title':'NOAA Coral Reef Watch','url':'https://coralreefwatch.noaa.gov/','hazard_types':['marine-heatwave','coral-heat-stress'],'limitations':'Thermal stress products do not by themselves prove observed bleaching or mortality.'},
        {'id':'noaa-coastwatch','title':'NOAA CoastWatch / OceanWatch','url':'https://coastwatch.noaa.gov/','hazard_types':['marine-heatwave','sea-ice-anomaly','extreme-waves','storm-ocean-impact','ecosystem-change'],'limitations':'A gridded anomaly is not an official hazard declaration.'},
        {'id':'copernicus-marine','title':'Copernicus Marine Service','url':'https://marine.copernicus.eu/','hazard_types':['marine-heatwave','hypoxia','sea-ice-anomaly','extreme-waves','ecosystem-change'],'limitations':'Model, analysis and forecast products remain distinct from in-situ observations.'},
        {'id':'noaa-nccos','title':'NOAA National Centers for Coastal Ocean Science','url':'https://coastalscience.noaa.gov/','hazard_types':['harmful-algal-bloom','hypoxia','ecosystem-change'],'limitations':'A signal is not automatically a confirmed bloom or hypoxic event.'},
      ],
      'hazard_types':[
        {'id':'marine-heatwave','title':'Marine heatwave / thermal anomaly'},{'id':'coral-heat-stress','title':'Coral bleaching heat stress'},
        {'id':'harmful-algal-bloom','title':'Harmful algal bloom'},{'id':'hypoxia','title':'Hypoxia / low dissolved oxygen'},
        {'id':'sea-ice-anomaly','title':'Sea-ice anomaly'},{'id':'extreme-waves','title':'Extreme wave conditions'},
        {'id':'storm-ocean-impact','title':'Storm-driven ocean impact'},{'id':'ecosystem-change','title':'Ecosystem change signal'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'noaa-coral-reef-watch',hazard=qp.get('hazard_type')||'marine-heatwave',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],h=catalog.hazard_types.find(r=>r.id===hazard)||catalog.hazard_types[0];x={ok:true,version:'4.17.0',contract:'ocean-events-hazards-ecosystem-change',source:s,hazard_type:h,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_hazard_type:(s.hazard_types||[]).includes(h.id),evidence:{condition_record_loaded:false,source_event_loaded:false,threshold_evaluated:false,official_advisory_loaded:false,ecosystem_impact_observed:false},truth:{hazard_declared:false,warning_issued_by_platform:false,forecast_treated_as_observation:false,model_treated_as_in_situ:false,threshold_treated_as_event:false,zero_records_treated_as_safe:false,source_advisory_reissued_by_platform:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="oceanMissionsPanel"><div class="om41000-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIOceanEventsV41100?.version==='4.17.0'")
    page.locator('#omEventsEnter').click()
    page.wait_for_function("!document.querySelector('#oceanEventsPanel').hidden")
    page.select_option('#oeSource','noaa-nccos'); page.select_option('#oeHazard','harmful-algal-bloom')
    page.fill('#oeLat','27.8'); page.fill('#oeLon','-82.6'); page.locator('#oeLon').dispatch_event('change'); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#oeStateTitle')?.textContent.includes('National Centers')")
    m=page.evaluate("""()=>({version:SCSIOceanEventsV41100.version,source:document.querySelector('#oeSource').value,hazard:document.querySelector('#oeHazard').value,stage:document.querySelector('#oeStageState').textContent,truth:document.querySelector('#oeTruth').textContent,contract:document.querySelector('#oceanEventsPanel').dataset.scsiOceanEventsContract,hidden:document.querySelector('#oceanEventsPanel').hidden})""")
    assert m['version']=='4.17.0' and m['source']=='noaa-nccos' and m['hazard']=='harmful-algal-bloom'
    assert 'no condition or event evidence loaded' in m['stage'].lower()
    assert 'Hazard declared' in m['truth'] and 'Platform warning' in m['truth'] and 'Zero records = safe' in m['truth'] and 'Observed ecosystem impact' in m['truth']
    assert m['contract']=='ocean-events-hazards-ecosystem-change' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.17.0 Ocean Events, Hazards & Ecosystem Change passed direct and iframe interaction.'); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
