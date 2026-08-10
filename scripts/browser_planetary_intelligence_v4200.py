from pathlib import Path
import json, os, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/planetary-intelligence-v4200.js').read_text()
CSS=(ROOT/'backend/public_app/assets/planetary-intelligence-v4200.css').read_text()
def browser_path():
    for p in ['/usr/bin/chromium','/usr/bin/google-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists(): return p
    return None
def fixture_html():
    moon={"ok":True,"body_id":"moon","body":{"title":"Moon","products":[{"id":"lro-wac-morphology","title":"LRO WAC","mission":"Lunar Reconnaissance Orbiter","instrument":"LROC WAC","product_type":"global image mosaic","resolution":"100 m/pixel","coverage":"global","source":"USGS Astrogeology","source_url":"https://astrogeology.usgs.gov/x","quantitative_use":"context"}]}}
    mars={"ok":True,"body_id":"mars","body":{"title":"Mars","products":[{"id":"themis-controlled","title":"THEMIS Controlled IR","mission":"2001 Mars Odyssey","instrument":"THEMIS","product_type":"controlled qualitative infrared mosaic","resolution":"100 m/pixel","coverage":"regional","source":"USGS Astrogeology","source_url":"https://stac.astrogeology.usgs.gov/x","quantitative_use":"8-bit qualitative"}]}}
    base={"ok":True,"version":"4.13.0","contract":"lunar-planetary-intelligence","mode":"planetary","body_id":"moon","body_title":"Moon","view":{"center":[0.0,0.0],"zoom":2.0,"not_earth_coordinates":True},"observation":{**moon['body']['products'][0],"official_imagery_url":"https://trek.nasa.gov/moon/","embedded_verified_raster":False},"truth":{"local_surface_texture_is_mission_imagery":False,"official_source_handoff_available":True}}
    setup=f'''<script>history.replaceState=()=>{{}};Element.prototype.scrollIntoView=()=>{{}};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;const moon={json.dumps(moon)},mars={json.dumps(mars)},base={json.dumps(base)};window.fetch=async input=>{{const u=String(input);let x=base;if(u.includes('/body/mars'))x=mars;else if(u.includes('/body/moon'))x=moon;else if(u.includes('body=mars'))x={{...base,body_id:'mars',body_title:'Mars',view:{{center:[0,137.4],zoom:2,not_earth_coordinates:true}},observation:{{...mars.body.products[0],official_imagery_url:'https://trek.nasa.gov/mars/',embedded_verified_raster:false}}}};return new Response(JSON.stringify(x),{{status:200,headers:{{'Content-Type':'application/json'}}}})}};</script>'''
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="earthOrbitPanel"></section><button id="earthPlanetaryEnter">Moon & Mars</button><section id="planetaryPanel" class="planetary-panel" hidden></section><script>{JS}</script></body></html>'''
def exercise(page,label):
    page.set_content(fixture_html(), wait_until='domcontentloaded')
    page.wait_for_function("window.SCSIPlanetaryV4200?.version==='4.13.0'")
    page.locator('#earthPlanetaryEnter').click()
    page.wait_for_function("!document.querySelector('#planetaryPanel').hidden")
    page.wait_for_function("document.querySelector('#planetaryMission').textContent.includes('Lunar Reconnaissance')")
    page.select_option('#planetaryBody','mars')
    page.wait_for_function("document.querySelector('#planetaryBodyTitle').textContent==='Mars'")
    m=page.evaluate("""()=>({version:SCSIPlanetaryV4200.version,body:document.querySelector('#planetaryBodyTitle').textContent,mission:document.querySelector('#planetaryMission').textContent,truth:document.querySelector('#planetaryTruth').textContent,hidden:document.querySelector('#planetaryPanel').hidden})""")
    assert m['version']=='4.13.0' and m['body']=='Mars' and 'Mars Odyssey' in m['mission'] and 'Orientation only' in m['truth'] and not m['hidden']
    return {'label':label,**m}
def main():
    path=browser_path()
    if not path: print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,executable_path=path,args=['--no-sandbox','--disable-dev-shm-usage'])
    direct=browser.new_page(viewport={'width':1200,'height':850}); r1=exercise(direct,'direct')
    outer=browser.new_page(viewport={'width':1200,'height':850}); outer.set_content('<iframe id="f" style="width:1100px;height:760px"></iframe>'); frame=outer.query_selector('#f').content_frame(); r2=exercise(frame,'iframe')
    print(json.dumps({'browser':path,'results':[r1,r2]},indent=2)); print('PASS: v4.13.0 Lunar & Planetary Intelligence passed direct and iframe interaction.')
    sys.stdout.flush(); os._exit(0)
if __name__=='__main__':
    try: status=main()
    except BaseException: traceback.print_exc(); status=1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
