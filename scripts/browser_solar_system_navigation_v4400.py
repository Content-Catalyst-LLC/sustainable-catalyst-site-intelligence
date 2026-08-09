from pathlib import Path
import json, os, sys, traceback

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'backend/public_app/assets/solar-system-navigation-v4400.js').read_text()
CSS = (ROOT / 'backend/public_app/assets/solar-system-navigation-v4400.css').read_text()


def browser_path():
    for p in ['/usr/bin/chromium', '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if Path(p).exists():
            return p
    return None


def fixture_html():
    bodies = [
        {'id':'sun','title':'Sun','naif_id':10},
        {'id':'earth','title':'Earth','naif_id':399},
        {'id':'mars','title':'Mars','naif_id':499},
        {'id':'jupiter','title':'Jupiter','naif_id':599},
        {'id':'saturn','title':'Saturn','naif_id':699},
    ]
    catalog = {
        'ok': True, 'version': '4.11.0', 'bodies': bodies,
        'missions': [
            {'id':'juno','title':'Juno'},
            {'id':'voyager-1','title':'Voyager 1'},
        ],
        'frames': [{'id':'J2000'}, {'id':'ECLIPJ2000'}, {'id':'BODY-FIXED'}],
        'observers': [
            {'id':'solar-system-barycenter','title':'solar-system barycenter'},
            {'id':'sun-center','title':'Sun center'},
            {'id':'earth-center','title':'Earth center'},
        ],
    }
    setup = r'''<script>
history.replaceState=()=>{};Element.prototype.scrollIntoView=()=>{};window.SC_SITE_INTELLIGENCE_API='https://gate.local';window.open=()=>null;window.matchMedia=()=>({matches:true});
const catalog=__CATALOG__,bodies=__BODIES__;
window.fetch=async input=>{const u=String(input);let x=catalog;if(u.includes('/state')){const q=new URL(u).searchParams;const body=q.get('body')||'earth';const mission=q.get('mission')||'';const row=bodies.find(b=>b.id===body)||bodies[1];x={ok:true,version:'4.11.0',body:row,mission:mission?{id:mission,title:mission==='juno'?'Juno':'Voyager 1'}:null,time:{epoch_utc:q.get('epoch')?q.get('epoch')+':00Z':null},view:{frame:q.get('frame')||'J2000',observer:{id:q.get('observer')||'solar-system-barycenter',title:q.get('observer')||'solar-system barycenter'}},ephemeris:{authorities:[{id:'jpl-horizons',url:'https://ssd.jpl.nasa.gov/horizons/app.html'}]},exploration:{url:'https://eyes.nasa.gov/apps/solar-system/'},truth:{local_orbit_layout_is_ephemeris:false,spacecraft_position_fabricated:false,trajectory_fabricated:false}};}return new Response(JSON.stringify(x),{status:200,headers:{'Content-Type':'application/json'}})};
</script>'''.replace('__CATALOG__', json.dumps(catalog)).replace('__BODIES__', json.dumps(bodies))
    return f'''<!doctype html><html><head><style>{CSS}</style>{setup}</head><body><section id="astronomyPanel"></section><button id="earthSolarSystemEnter">Solar System</button><section id="solarSystemPanel" class="solar-system-panel" hidden></section><script>{JS}</script></body></html>'''


def exercise(page, label):
    page.set_content(fixture_html(), wait_until='domcontentloaded')
    page.wait_for_function("window.SCSISolarSystemV4400?.version==='4.11.0'")
    page.locator('#earthSolarSystemEnter').click()
    page.wait_for_function("!document.querySelector('#solarSystemPanel').hidden")
    page.wait_for_function("document.querySelector('#solarTargetTitle').textContent.includes('Earth')")
    page.select_option('#solarBody', 'jupiter')
    page.select_option('#solarMission', 'juno')
    page.select_option('#solarFrame', 'ECLIPJ2000')
    page.select_option('#solarObserver', 'earth-center')
    page.fill('#solarEpoch', '2026-08-09T06:32')
    page.locator('#solarEpoch').dispatch_event('change')
    page.wait_for_function("document.querySelector('#solarTargetTitle').textContent.includes('Juno')")
    page.wait_for_function("document.querySelector('#solarStateTitle').textContent.includes('Jupiter')")
    m = page.evaluate("""()=>({
      version:SCSISolarSystemV4400.version,
      target:document.querySelector('#solarTargetTitle').textContent,
      state:document.querySelector('#solarStateTitle').textContent,
      truth:document.querySelector('#solarTruth').textContent,
      stage:document.querySelector('.solar4400-stage-copy span').textContent,
      selected:document.querySelector('.solar4400-body.is-selected')?.dataset.body,
      frame:document.querySelector('#solarFrame').value,
      observer:document.querySelector('#solarObserver').value,
      hidden:document.querySelector('#solarSystemPanel').hidden
    })""")
    assert m['version'] == '4.11.0'
    assert 'Juno' in m['target'] and 'Jupiter' in m['state']
    assert 'Not claimed' in m['truth'] and 'Not rendered' in m['truth']
    assert 'NOT EPHEMERIS' in m['stage'] and m['selected'] == 'jupiter'
    assert m['frame'] == 'ECLIPJ2000' and m['observer'] == 'earth-center' and not m['hidden']
    return {'label': label, **m}


def main():
    path = browser_path()
    if not path:
        print('SKIP: Chromium unavailable')
        return 0
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, executable_path=path, args=['--no-sandbox', '--disable-dev-shm-usage'])
    direct = browser.new_page(viewport={'width':1200,'height':850})
    r1 = exercise(direct, 'direct')
    outer = browser.new_page(viewport={'width':1200,'height':850})
    outer.set_content('<iframe id="f" style="width:1100px;height:760px"></iframe>')
    frame = outer.query_selector('#f').content_frame()
    r2 = exercise(frame, 'iframe')
    print(json.dumps({'browser': path, 'results': [r1, r2]}, indent=2))
    print('PASS: v4.11.0 Solar System Navigation & Mission Ephemeris passed direct and iframe interaction.')
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    try:
        status = main()
    except BaseException:
        traceback.print_exc()
        status = 1
    sys.stdout.flush(); sys.stderr.flush(); os._exit(status or 0)
