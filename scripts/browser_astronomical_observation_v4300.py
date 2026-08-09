from pathlib import Path
import json, os, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text()
CSS=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.css').read_text()

def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None

def fixture_html():
    catalog={
        "ok":True,"version":"4.6.0",
        "targets":[{"id":"m31","title":"Andromeda Galaxy (M31)"},{"id":"crab","title":"Crab Nebula (M1)"}],
        "surveys":[{"id":"dss-optical","title":"Digitized Sky Survey","wavelength":"optical"},{"id":"rosat-soft-xray","title":"ROSAT soft X-ray survey family","wavelength":"soft X-ray"}]
    }
    base={
        "ok":True,"version":"4.6.0",
        "target":{"target_id":"m31","title":"Andromeda Galaxy (M31)","ra_deg":10.684708,"dec_deg":41.26875},
        "view":{"field_deg":0.25,"coordinate_frame":"equatorial J2000"},
        "observation":{"id":"dss-optical","title":"Digitized Sky Survey","wavelength":"optical","archive":"NASA/IPAC IRSA Finder Chart","survey_family":"DSS","color_semantics":"single-band display; not natural color","official_observation_handoff":{"url":"https://irsa.ipac.caltech.edu/x"}}
    }
    setup="""<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;
const catalog=__CATALOG__,base=__BASE__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){x=JSON.parse(JSON.stringify(base));if(u.includes('crab'))x.target={target_id:'crab',title:'Crab Nebula (M1)',ra_deg:83.633083,dec_deg:22.0145};if(u.includes('rosat-soft-xray'))x.observation={id:'rosat-soft-xray',title:'ROSAT soft X-ray survey family',wavelength:'soft X-ray',archive:'NASA/GSFC HEASARC SkyView',survey_family:'ROSAT',color_semantics:'X-ray intensity; display color is representational',official_observation_handoff:{url:'https://skyview.gsfc.nasa.gov/current/cgi/basicform.pl'}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>""".replace('__CATALOG__',json.dumps(catalog)).replace('__BASE__',json.dumps(base))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="planetaryPanel"></section><button id="earthAstronomyEnter">Deep Sky</button><section id="astronomyPanel" class="astronomy-panel" hidden></section><script>{JS}</script></body></html>'''

def exercise(page,label):
    page.set_content(fixture_html(), wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIAstronomicalV4300?.version==='4.6.0'")
    page.locator('#earthAstronomyEnter').click()
    page.wait_for_function("!document.querySelector('#astronomyPanel').hidden")
    page.wait_for_function("document.querySelector('#astroTargetTitle').textContent.includes('Andromeda')")
    page.select_option('#astroTarget','crab')
    page.select_option('#astroSurvey','rosat-soft-xray')
    page.wait_for_function("document.querySelector('#astroSurveyTitle').textContent.includes('ROSAT')")
    m=page.evaluate("""()=>({version:SCSIAstronomicalV4300.version,target:document.querySelector('#astroTargetTitle').textContent,survey:document.querySelector('#astroSurveyTitle').textContent,truth:document.querySelector('#astroTruth').textContent,stage:document.querySelector('.astro4300-stage-copy span').textContent,hidden:document.querySelector('#astronomyPanel').hidden})""")
    assert m['version']=='4.6.0' and 'Crab' in m['target'] and 'ROSAT' in m['survey'] and 'Orientation only' in m['truth'] and 'NOT SURVEY PIXELS' in m['stage'] and not m['hidden']
    return {'label':label,**m}

def main():
    path=browser_path()
    if not path:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start()
    browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':850}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':850}); outer.set_content('<iframe id="f" style="width:1100px;height:760px"></iframe>')
    frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2))
    print('PASS: v4.6.0 Astronomical Observation Environment passed direct and iframe interaction.')
    sys.stdout.flush(); os._exit(0)

if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
