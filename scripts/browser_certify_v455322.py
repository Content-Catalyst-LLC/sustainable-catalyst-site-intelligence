#!/usr/bin/env python3
from __future__ import annotations

import json, re
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
API_HOST='site-intelligence-api.sustainablecatalyst.com'
VERSION='4.56.0'
OPTIONAL_FAILURES={'/public/build-info','/public/deployment-receipt','/public/runtime-recovery'}

def api_payload(url: str):
    path=urlparse(url).path
    base={"ok":True,"version":VERSION,"records":[],"items":[],"results":[],"events":[],"layers":[],"sources":[],"count":0,"total":0,"state":"connected"}
    if path=='/health':
        return 200,{**base,"alive":True,"scope":"process-only"}
    if path in OPTIONAL_FAILURES:
        return 503,{"ok":False,"version":VERSION,"state":"degraded","detail":"fixture optional diagnostic unavailable"}
    if path=='/public/app/bootstrap':
        return 200,{**base,"runtime":{"mode":"standalone"},"authority":{"backend":"fastapi"},"capability_registry":{"version":"2.6.2","route_count":1518},"navigation":{"items":[]},"session":{}}
    if path=='/public/app/runtime-handshake':
        return 200,{**base,"compatible":True,"client_version":VERSION}
    if path=='/public/runtime-health':
        return 200,{**base,"status":"healthy"}
    if path=='/public/economics-sustainability':
        return 200,{**base,"counts":{"records_available":0,"sources_visible":0,"geographies_visible":0,"indicators_visible":0},"integration":{"state":"connected","message":"Core economics and official-statistics records are available through the Site Intelligence public bridge."},"families":[],"market_data_policy":{"statement":"Official releases only."}}
    if path=='/public/economics-sustainability/facets':
        return 200,{**base,"families":[],"sources":[],"frequencies":[],"indicators":[]}
    if path=='/public/countries':
        return 200,{**base,"countries":[{"code":"KEN","name":"Kenya","display_name":"Kenya","latitude":0.0236,"longitude":37.9062},{"code":"IRL","name":"Ireland","display_name":"Ireland","latitude":53.3,"longitude":-8.0}]}
    if path=='/public/reliable/economics/records':
        return 200,{**base,"contract_schema":"sc-site-intelligence-reliable-response/1.1","contract_version":VERSION,"capability":"economics","dependency_state":"connected","data_state":"no-records","record_count":0,"records":[],"integration":{"state":"connected","message":"Core economics and official-statistics records are available through the Site Intelligence public bridge."},"context_resolution":{"requested":"KEN","iso3":"KEN","iso2":"KE","name":"Kenya","resolved":True}}
    if path=='/public/performance-offline':
        return 200,{**base,"performance_budgets":{"first_useful_map_ms":3500}}
    if path=='/public/workspaces/production-truth':
        return 200,{**base,"routes":[]}
    return 200,base

def inline_local_scripts(html: str) -> str:
    def css_repl(match):
        href=(match.group(1) or match.group(2)).split('?',1)[0]
        if href.startswith('/app/'):
            path=WEB/href.lstrip('/')
            if path.is_file(): return '<style>\n'+path.read_text()+'\n</style>'
        return ''
    html=re.sub(r'<link[^>]+href="([^"]+)"[^>]*rel="stylesheet"[^>]*>|<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"[^>]*>',css_repl,html)
    def repl(match):
        src=match.group(1).split('?',1)[0]
        if src=='/config.js': path=WEB/'config.js'
        elif src.startswith('/app/'): path=WEB/src.lstrip('/')
        else: return match.group(0)
        if not path.is_file(): return match.group(0)
        return '<script>\n'+path.read_text()+'\n</script>'
    return re.sub(r'<script[^>]+src="([^"]+)"[^>]*></script>',repl,html)

def main():
    errors=[]
    with sync_playwright() as p:
        
        launch_kwargs={'headless':True,'args':['--no-sandbox']}
        if Path('/usr/bin/chromium').exists(): launch_kwargs['executable_path']='/usr/bin/chromium'
        browser=p.chromium.launch(**launch_kwargs)
        page=browser.new_page(viewport={"width":1440,"height":1000})
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.goto('about:blank?view=economics&country=KEN&geography_code=KEN')
        page.evaluate('''() => {
          const makeStore=()=>{const d={};return {getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{for(const k of Object.keys(d))delete d[k]},key:i=>Object.keys(d)[i]||null,get length(){return Object.keys(d).length}}};
          Object.defineProperty(window,'localStorage',{value:makeStore(),configurable:true});
          Object.defineProperty(window,'sessionStorage',{value:makeStore(),configurable:true});
        }''')
        def api_route(route):
            status,payload=api_payload(route.request.url)
            route.fulfill(status=status,content_type='application/json',body=json.dumps(payload))
        page.route(f'https://{API_HOST}/**',api_route)
        page.route('https://*.tile.openstreetmap.org/**',lambda route: route.fulfill(status=204,body=''))
        page.route('https://gibs.earthdata.nasa.gov/**',lambda route: route.fulfill(status=204,body=''))
        html=inline_local_scripts((WEB/'index.html').read_text())
        page.set_content(html,wait_until='domcontentloaded',timeout=30000)
        page.wait_for_selector('#economicsStudio:not([hidden])',timeout=15000)
        page.wait_for_timeout(1800)

        assert page.evaluate('()=>window.SCSIStandaloneBridgeV455321?.version')==VERSION
        assert page.locator('#economicsCountry').input_value()=='KEN'
        assert page.locator('#economicsRecordCount').inner_text().strip()=='0'
        economics_status=page.locator('#economicsStatus').inner_text().lower()
        assert 'no official economics records matched kenya' in economics_status,economics_status
        assert page.locator('#economicsStatus').get_attribute('data-state')!='ready'

        page.evaluate('()=>window.SCSIRuntimeHealth?.run?.()')
        page.wait_for_timeout(9000)
        report=page.evaluate('()=>window.SCSIRuntimeHealth?.report?.()')
        assert report and report['online'] is True
        assert report['overallStatus']=='degraded',report
        label=page.locator('#scsiRuntimeToggle [data-runtime-toggle-label]').inner_text()
        assert label=='Site health: Degraded',label

        # Global country changes propagate into the active Economics filter.
        page.evaluate('''() => { const s=document.querySelector('#countrySelect'); if(![...s.options].some(o=>o.value==='IRL')){const o=document.createElement('option');o.value='IRL';o.textContent='Ireland';s.appendChild(o)} s.value='IRL'; s.dispatchEvent(new Event('change',{bubbles:true})); }''')
        page.wait_for_timeout(800)
        assert page.locator('#economicsCountry').input_value()=='IRL'
        assert page.evaluate('()=>new URL(location.href).searchParams.get("geography_code")')=='IRL'

        rewritten=page.evaluate("()=>window.SCSIStandaloneBridgeV455321.toApi('/public/economics-sustainability/records?geography_code=KEN')")
        assert '/public/reliable/economics/records?geography_code=KEN' in rewritten
        fatal=[e for e in errors if 'SyntaxError' in e or 'ReferenceError' in e]
        assert not fatal,fatal
        browser.close()
    print('V455322_BROWSER_CERTIFICATION=PASS')

if __name__=='__main__': main()
