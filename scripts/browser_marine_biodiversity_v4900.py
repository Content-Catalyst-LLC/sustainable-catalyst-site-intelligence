#!/usr/bin/env python3
from pathlib import Path
import json, os, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/marine-biodiversity-v4900.js').read_text()
CSS=(ROOT/'backend/public_app/assets/marine-biodiversity-v4900.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
      'ok':True,'version':'4.16.0','contract':'marine-biodiversity-bioacoustic-intelligence',
      'sources':[
        {'id':'obis','title':'Ocean Biodiversity Information System (OBIS)','url':'https://obis.org/','limitations':'Occurrence records are not abundance or continued-presence claims.'},
        {'id':'worms','title':'World Register of Marine Species (WoRMS)','url':'https://www.marinespecies.org/','limitations':'Taxonomy is not occurrence evidence.'},
        {'id':'fathomnet','title':'FathomNet visual biodiversity evidence','url':'https://www.fathomnet.org/','limitations':'Model labels are not verified species observations.'},
        {'id':'onc-hydrophones','title':'Ocean Networks Canada hydrophones','url':'https://data.oceannetworks.ca/','limitations':'A recording is not itself a biological detection.'},
      ],
      'evidence_classes':[
        {'id':'occurrence-record','title':'Occurrence record'},{'id':'taxonomy-record','title':'Taxonomy record'},
        {'id':'visual-annotation','title':'Visual annotation'},{'id':'acoustic-recording','title':'Acoustic recording'},
        {'id':'acoustic-detection','title':'Acoustic detection'},{'id':'environmental-context','title':'Environmental context'}]}
    setup='''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const qp=new URL(u).searchParams,source=qp.get('source')||'obis',evidence=qp.get('evidence_class')||'occurrence-record',s=catalog.sources.find(r=>r.id===source)||catalog.sources[0],e=catalog.evidence_classes.find(r=>r.id===evidence)||catalog.evidence_classes[0];x={ok:true,version:'4.16.0',contract:'marine-biodiversity-bioacoustic-intelligence',source:s,evidence_class:e,scientific_name:qp.get('scientific_name')||null,point:qp.has('latitude')?{latitude:Number(qp.get('latitude')),longitude:Number(qp.get('longitude'))}:null,depth_m:qp.has('depth_m')?Number(qp.get('depth_m')):null,date:qp.get('date')||null,evidence:{records_loaded:false,record_count:null,presence_verified:false,absence_verified:false,abundance_verified:false,taxonomy_verified:false,acoustic_detection_verified:false},truth:{zero_results_as_absence:false,annotation_as_occurrence:false,model_detection_as_verified_species:false,recording_as_detection:false,detection_as_abundance:false,taxonomy_as_occurrence:false,environmental_context_assumed_synchronized:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__',json.dumps(catalog))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="underwaterObservationPanel"><div class="uw4800-actions"><button>Back</button></div></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(),wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIMarineBiodiversityV4900?.version==='4.16.0'")
    page.locator('#uwBiodiversityEnter').click()
    page.wait_for_function("!document.querySelector('#marineBiodiversityPanel').hidden")
    page.select_option('#bioSource','onc-hydrophones'); page.select_option('#bioEvidence','acoustic-detection')
    page.fill('#bioName','Orcinus orca'); page.fill('#bioDepth','900'); page.fill('#bioLat','48.5'); page.fill('#bioLon','-126.2')
    page.locator('#bioLon').dispatch_event('change'); page.wait_for_timeout(120)
    page.wait_for_function("document.querySelector('#bioStateTitle')?.textContent.includes('Ocean Networks Canada')")
    m=page.evaluate("""()=>({version:SCSIMarineBiodiversityV4900.version,source:document.querySelector('#bioSource').value,evidence:document.querySelector('#bioEvidence').value,name:document.querySelector('#bioName').value,stage:document.querySelector('#bioStageState').textContent,truth:document.querySelector('#bioTruth').textContent,contract:document.querySelector('#marineBiodiversityPanel').dataset.scsiBiodiversityContract,hidden:document.querySelector('#marineBiodiversityPanel').hidden})""")
    assert m['version']=='4.16.0' and m['source']=='onc-hydrophones' and m['evidence']=='acoustic-detection'
    assert m['name']=='Orcinus orca' and 'no evidence records loaded' in m['stage'].lower()
    assert 'Not verified' in m['truth'] and 'Zero records = absence' in m['truth'] and 'No' in m['truth']
    assert m['contract']=='marine-biodiversity-bioacoustic-intelligence' and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':900}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':900}); outer.set_content('<iframe id="f" style="width:1100px;height:820px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.16.0 Marine Biodiversity & Bioacoustic Intelligence passed direct and iframe interaction.'); sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
