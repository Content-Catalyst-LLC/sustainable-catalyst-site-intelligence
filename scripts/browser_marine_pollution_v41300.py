#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/marine-pollution-v41300.js').read_text()
CSS=(ROOT/'backend/public_app/assets/marine-pollution-v41300.css').read_text()


def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None


def fixture_html():
    catalog={
      'ok':True,'version':'4.13.0','contract':'marine-pollution-debris-water-quality',
      'sources':[
        {'id':'noaa-ncei-marine-microplastics','title':'NOAA NCEI Marine Microplastics','url':'https://www.ncei.noaa.gov/products/microplastics','indicator_types':['microplastics'],'limitations':'Missing records do not establish clean water.'},
        {'id':'emodnet-chemistry','title':'EMODnet Chemistry','url':'https://emodnet.ec.europa.eu/en/chemistry','indicator_types':['heavy-metals','seafloor-litter'],'limitations':'Matrices, methods, flags and coverage vary.'},
        {'id':'copernicus-marine-biogeochemistry','title':'Copernicus Marine Biogeochemistry','url':'https://data.marine.copernicus.eu/','indicator_types':['nutrients','dissolved-oxygen','ph-acidity','chlorophyll'],'limitations':'Model analyses and forecasts are not in-situ samples.'},
        {'id':'water-quality-portal','title':'Water Quality Portal','url':'https://www.waterqualitydata.us/','indicator_types':['water-quality','heavy-metals','nutrients'],'limitations':'The portal is not marine-only.'},
      ],
      'indicator_types':[
        {'id':'microplastics','title':'Microplastics'},{'id':'seafloor-litter','title':'Seafloor litter'},
        {'id':'heavy-metals','title':'Heavy metals'},{'id':'nutrients','title':'Nutrients / eutrophication context'},
        {'id':'dissolved-oxygen','title':'Dissolved oxygen'},{'id':'ph-acidity','title':'pH / acidity'},
        {'id':'chlorophyll','title':'Chlorophyll'},{'id':'water-quality','title':'General water-quality sample'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'noaa-ncei-marine-microplastics',indicator=qp.get('indicator_type')||'microplastics',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],a=catalog.indicator_types.find(r=>r.id===indicator)||catalog.indicator_types[0];x={ok:true,version:'4.13.0',contract:'marine-pollution-debris-water-quality',source:s,indicator_type:a,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_indicator_type:(s.indicator_types||[]).includes(a.id),evidence:{measurement_loaded:false,debris_record_loaded:false,non_detect_loaded:false,quality_flag_loaded:false,threshold_evaluated:false,regulatory_standard_loaded:false,health_advisory_loaded:false},truth:{zero_records_treated_as_clean_water:false,non_detect_treated_as_zero:false,model_treated_as_in_situ_sample:false,debris_source_attributed_by_platform:false,threshold_treated_as_regulatory_exceedance:false,platform_health_risk_finding:false,platform_ecological_harm_finding:false,platform_compliance_finding:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="marineHumanActivityPanel"><div class="mh41200-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''


def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIMarinePollutionV41300?.version==='4.13.0'")
    page.locator('#mhPollutionEnter').click()
    page.wait_for_function("!document.querySelector('#marinePollutionPanel').hidden")
    page.select_option('#mpSource','emodnet-chemistry'); page.select_option('#mpIndicator','heavy-metals')
    page.fill('#mpLat','54.0'); page.fill('#mpLon','5.0'); page.locator('#mpLon').dispatch_event('change'); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#mpStateTitle')?.textContent.includes('EMODnet')")
    m=page.evaluate("""()=>({version:SCSIMarinePollutionV41300.version,source:document.querySelector('#mpSource').value,indicator:document.querySelector('#mpIndicator').value,stage:document.querySelector('#mpStageState').textContent,truth:document.querySelector('#mpTruth').textContent,contract:document.querySelector('#marinePollutionPanel').dataset.scsiMarinePollutionContract,hidden:document.querySelector('#marinePollutionPanel').hidden})""")
    assert m['version']=='4.13.0' and m['source']=='emodnet-chemistry' and m['indicator']=='heavy-metals'
    assert 'no pollution measurement or debris evidence loaded' in m['stage'].lower()
    assert 'Zero records = clean water' in m['truth'] and 'Non-detect = zero' in m['truth'] and 'Health-risk finding' in m['truth'] and 'Compliance finding' in m['truth']
    assert m['contract']=='marine-pollution-debris-water-quality' and not m['hidden']
    return {'label':label,**m}


def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.13.0 Marine Pollution passed direct and iframe interaction.'); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
