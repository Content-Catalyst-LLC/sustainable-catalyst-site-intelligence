#!/usr/bin/env python3
from pathlib import Path
import json, os, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/ocean-missions-v41000.js').read_text()
CSS=(ROOT/'backend/public_app/assets/ocean-missions-v41000.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.11.0','contract':'ocean-missions-vehicles-observatory-network',
      'sources':[
        {'id':'argo','title':'Argo observing network / Argovis access','url':'https://argo.ucsd.edu/data/','platform_types':['float'],'limitations':'A most-recent reported float position is not a verified current position.'},
        {'id':'ioos','title':'U.S. Integrated Ocean Observing System (IOOS)','url':'https://ioos.noaa.gov/data/access-ioos-data/','platform_types':['glider','buoy','mooring','fixed-observatory'],'limitations':'Registry presence does not prove current operation.'},
        {'id':'onc','title':'Ocean Networks Canada Oceans 3.0','url':'https://data.oceannetworks.ca/','platform_types':['fixed-observatory','camera-station','hydrophone-station','auv','rov'],'limitations':'A deployment/device record does not establish current operational state.'},
        {'id':'noaa-ocean-exploration','title':'NOAA Ocean Exploration','url':'https://oceanexplorer.noaa.gov/data/access-tools/','platform_types':['research-vessel','rov','auv'],'limitations':'An archived expedition or dive track is historical evidence, not a live vehicle feed.'},
      ],
      'platform_types':[
        {'id':'float','title':'Profiling float'},{'id':'glider','title':'Ocean glider'},{'id':'buoy','title':'Buoy'},
        {'id':'mooring','title':'Mooring'},{'id':'auv','title':'Autonomous underwater vehicle'},{'id':'rov','title':'Remotely operated vehicle'},
        {'id':'research-vessel','title':'Research vessel'},{'id':'fixed-observatory','title':'Fixed observatory'},
        {'id':'camera-station','title':'Underwater camera station'},{'id':'hydrophone-station','title':'Hydrophone station'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'argo',type=qp.get('platform_type')||'float',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],t=catalog.platform_types.find(r=>r.id===type)||catalog.platform_types[0];x={ok:true,version:'4.11.0',contract:'ocean-missions-vehicles-observatory-network',source:s,platform_type:t,platform_id:qp.get('platform_id')||null,query_point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,date:qp.get('date')||null,source_supports_platform_type:(s.platform_types||[]).includes(t.id),evidence:{platform_record_loaded:false,mission_record_loaded:false,position_record_loaded:false,track_loaded:false,operational_status_loaded:false},truth:{current_position_verified:false,current_operational_status_verified:false,continuous_trajectory_verified:false,future_trajectory_predicted:false,nearby_observation_as_platform_position:false,registry_presence_as_active_operation:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="marineBiodiversityPanel"><div class="bio4900-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIOceanMissionsV41000?.version==='4.11.0'")
    page.locator('#bioMissionsEnter').click()
    page.wait_for_function("!document.querySelector('#oceanMissionsPanel').hidden")
    page.select_option('#omSource','argo'); page.select_option('#omType','float')
    page.fill('#omPlatform','5901234'); page.fill('#omLat','35.1'); page.fill('#omLon','-145.2')
    page.locator('#omLon').dispatch_event('change'); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#omStateTitle')?.textContent.includes('Argo')")
    m=page.evaluate("""()=>({version:SCSIOceanMissionsV41000.version,source:document.querySelector('#omSource').value,type:document.querySelector('#omType').value,platform:document.querySelector('#omPlatform').value,stage:document.querySelector('#omStageState').textContent,truth:document.querySelector('#omTruth').textContent,contract:document.querySelector('#oceanMissionsPanel').dataset.scsiOceanMissionsContract,hidden:document.querySelector('#oceanMissionsPanel').hidden})""")
    assert m['version']=='4.11.0' and m['source']=='argo' and m['type']=='float'
    assert m['platform']=='5901234' and 'no platform telemetry loaded' in m['stage'].lower()
    assert 'Current position' in m['truth'] and 'Not verified' in m['truth'] and 'Future position' in m['truth'] and 'Not predicted' in m['truth']
    assert m['contract']=='ocean-missions-vehicles-observatory-network' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.11.0 Ocean Missions, Vehicles & Observatory Network passed direct and iframe interaction.'); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    os._exit(status or 0)
