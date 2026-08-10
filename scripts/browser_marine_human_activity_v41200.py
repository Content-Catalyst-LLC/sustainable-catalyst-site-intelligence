#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/marine-human-activity-v41200.js').read_text()
CSS=(ROOT/'backend/public_app/assets/marine-human-activity-v41200.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.17.0','contract':'marine-human-activity-protected-areas-maritime-pressure',
      'sources':[
        {'id':'noaa-marine-cadastre-ais','title':'NOAA / BOEM Marine Cadastre Vessel Traffic','url':'https://hub.marinecadastre.gov/pages/vesseltraffic','activity_types':['vessel-traffic','port-traffic'],'limitations':'AIS is not a complete vessel census.'},
        {'id':'noaa-mpa-inventory','title':'NOAA Marine Protected Areas Inventory','url':'https://marineprotectedareas.noaa.gov/dataanalysis/mpainventory/','activity_types':['protected-area'],'limitations':'A boundary is not a legal opinion or navigational instruction.'},
        {'id':'emodnet-human-activities','title':'EMODnet Human Activities','url':'https://emodnet.ec.europa.eu/en/human-activities','activity_types':['vessel-traffic','port-traffic','offshore-energy','aquaculture','submarine-cables-pipelines','extraction-disposal','protected-area'],'limitations':'Coverage and refresh date vary by theme.'},
        {'id':'global-fishing-watch','title':'Global Fishing Watch APIs','url':'https://globalfishingwatch.org/our-apis/','activity_types':['vessel-traffic','fishing-activity','port-traffic'],'limitations':'Inferred fishing activity is not proof of illegal fishing.'},
      ],
      'activity_types':[
        {'id':'vessel-traffic','title':'Vessel traffic'},{'id':'fishing-activity','title':'Fishing activity'},
        {'id':'port-traffic','title':'Port traffic'},{'id':'offshore-energy','title':'Offshore energy'},
        {'id':'aquaculture','title':'Aquaculture'},{'id':'submarine-cables-pipelines','title':'Submarine cables & pipelines'},
        {'id':'extraction-disposal','title':'Extraction & disposal'},{'id':'protected-area','title':'Protected area / conservation zone'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'noaa-marine-cadastre-ais',activity=qp.get('activity_type')||'vessel-traffic',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],a=catalog.activity_types.find(r=>r.id===activity)||catalog.activity_types[0];x={ok:true,version:'4.17.0',contract:'marine-human-activity-protected-areas-maritime-pressure',source:s,activity_type:a,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_activity_type:(s.activity_types||[]).includes(a.id),evidence:{activity_record_loaded:false,protected_area_record_loaded:false,spatial_overlap_evaluated:false,legal_status_loaded:false,enforcement_record_loaded:false},truth:{ais_complete_vessel_census:false,zero_ais_treated_as_no_vessel:false,fishing_activity_treated_as_illegal:false,spatial_overlap_treated_as_violation:false,mapped_feature_treated_as_operational:false,platform_compliance_finding:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="oceanEventsPanel"><div class="oe41100-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIMarineHumanActivityV41200?.version==='4.17.0'")
    page.locator('#oeHumanEnter').click()
    page.wait_for_function("!document.querySelector('#marineHumanActivityPanel').hidden")
    page.select_option('#mhSource','global-fishing-watch'); page.select_option('#mhActivity','fishing-activity')
    page.fill('#mhLat','41.1'); page.fill('#mhLon','-69.2'); page.locator('#mhLon').dispatch_event('change'); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#mhStateTitle')?.textContent.includes('Global Fishing Watch')")
    m=page.evaluate("""()=>({version:SCSIMarineHumanActivityV41200.version,source:document.querySelector('#mhSource').value,activity:document.querySelector('#mhActivity').value,stage:document.querySelector('#mhStageState').textContent,truth:document.querySelector('#mhTruth').textContent,contract:document.querySelector('#marineHumanActivityPanel').dataset.scsiMarineHumanContract,hidden:document.querySelector('#marineHumanActivityPanel').hidden})""")
    assert m['version']=='4.17.0' and m['source']=='global-fishing-watch' and m['activity']=='fishing-activity'
    assert 'no activity or protected-area evidence loaded' in m['stage'].lower()
    assert 'Zero AIS = no vessel' in m['truth'] and 'Fishing activity = illegal' in m['truth'] and 'Overlap = violation' in m['truth'] and 'Compliance finding' in m['truth']
    assert m['contract']=='marine-human-activity-protected-areas-maritime-pressure' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.17.0 Marine Human Activity passed direct and iframe interaction.'); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
