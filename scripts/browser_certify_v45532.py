#!/usr/bin/env python3
from __future__ import annotations

import json, re
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'
API_HOST='site-intelligence-api.sustainablecatalyst.com'

def api_payload(url):
    path=urlparse(url).path
    base={"ok":True,"version":"4.55.3.2","records":[],"items":[],"results":[],"events":[],"layers":[],"sources":[],"countries":[{"code":"KEN","name":"Kenya","display_name":"Kenya"},{"code":"IRL","name":"Ireland","display_name":"Ireland"}],"facets":{},"count":0,"total":0,"state":"connected","integration":{"state":"connected","enabled":True,"configured":True},"capabilities":[]}
    if path=='/health': base.update({"alive":True,"state":"alive"})
    if '/public/app/bootstrap' in path:
        base.update({"runtime":{"mode":"standalone"},"capability_registry":{"route_count":1518},"navigation":{"items":[]}})
    if '/public/capability-health' in path:
        base.update({"overall_state":"degraded","usable_capabilities":5,"unavailable_capabilities":1,"partial_capabilities":2,"probe":True,"capabilities":[{"capability":"law","state":"degraded","data_state":"dependency-unavailable","http_status_if_requested":503}]})
    if '/public/web-app/parity' in path:
        base.update({"schema":"sc-site-intelligence-standalone-functional-parity/1.0","workspace_count":33,"functional_control_count":11})
    if '/public/intelligence-dossiers/facets' in path or path=='/public/countries':
        base.update({"countries":[{"code":"KEN","display_name":"Kenya","name":"Kenya"},{"code":"IRL","display_name":"Ireland","name":"Ireland"}]})
    if '/public/reliable/' in path:
        base.update({"contract_schema":"sc-site-intelligence-reliable-response/1.1","contract_version":"4.55.3.2","data_state":"no-records","record_count":0,"context_resolution":{"requested":"KEN","iso3":"KEN","iso2":"KE","name":"Kenya","resolved":True}})
    return base

def inline_local_scripts(html: str) -> str:
    def css_repl(match):
        href=match.group(1).split('?',1)[0]
        if href.startswith('/app/'):
            path=WEB/href.lstrip('/')
            if path.is_file(): return '<style>\n'+path.read_text()+'\n</style>'
        return ''
    html=re.sub(r'<link[^>]+href="([^"]+)"[^>]*rel="stylesheet"[^>]*>|<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"[^>]*>', lambda m: css_repl(type('M',(),{'group':lambda self,n: (m.group(1) or m.group(2))})()), html)
    def repl(match):
        src=match.group(1).split('?',1)[0]
        if src=='/config.js': path=WEB/'config.js'
        elif src.startswith('/app/'): path=WEB/src.lstrip('/')
        else: return match.group(0)
        if not path.is_file(): return match.group(0)
        return '<script>\n'+path.read_text()+'\n</script>'
    html=re.sub(r'<script[^>]+src="([^"]+)"[^>]*></script>', repl, html)
    return html

def main():
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page=browser.new_page(viewport={"width":1440,"height":1000})
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.evaluate('''() => {
          const makeStore=()=>{const d={};return {getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{for(const k of Object.keys(d))delete d[k]},key:i=>Object.keys(d)[i]||null,get length(){return Object.keys(d).length}}};
          Object.defineProperty(window,'localStorage',{value:makeStore(),configurable:true});
          Object.defineProperty(window,'sessionStorage',{value:makeStore(),configurable:true});
          History.prototype.replaceState=function(){}; History.prototype.pushState=function(){};
        }''')
        page.route(f'https://{API_HOST}/**', lambda route: route.fulfill(status=200,content_type='application/json',body=json.dumps(api_payload(route.request.url))))
        page.route('https://*.tile.openstreetmap.org/**',lambda route: route.fulfill(status=204,body=''))
        html=inline_local_scripts((WEB/'index.html').read_text())
        page.set_content(html,wait_until='domcontentloaded',timeout=30000)
        page.wait_for_selector('#primaryNavigation',state='attached',timeout=10000); page.wait_for_timeout(1800)
        assert page.locator('#primaryNavigation .nav-item').count() >= 30
        assert page.evaluate('()=>window.SCSIStandaloneBridgeV45532?.version')=='4.55.3.2'
        rewritten=page.evaluate("()=>window.SCSIStandaloneBridgeV45532.toApi('/public/economics-sustainability/records?geography_code=KEN')")
        assert '/public/reliable/economics/records?geography_code=KEN' in rewritten
        page.evaluate("()=>document.querySelector('[data-route=\"economics\"]').click()"); page.wait_for_timeout(800)
        assert not page.locator('#economicsStudio').get_attribute('hidden')
        page.evaluate("()=>document.querySelector('[data-route=\"science\"]').click()"); page.wait_for_timeout(800)
        assert not page.locator('#scienceStudio').get_attribute('hidden')
        page.evaluate("()=>window.SCSIRouterV3228?.navigate?.('research')"); page.wait_for_timeout(1800)
        assert page.evaluate('()=>window.SCSIRouterV3228?.current?.()')=='research'
        assert not page.locator('#researchWorkflowStudio').get_attribute('hidden')
        assert page.locator('[data-research-handoff="workbench"]').count()==1
        assert page.locator('#saveViewButton').is_enabled()
        assert page.locator('#shareButton').is_enabled()
        assert page.locator('#app').count()==1
        fatal=[e for e in errors if 'SyntaxError' in e or 'ReferenceError' in e]
        assert not fatal, fatal
        browser.close()
    print('V45532_BROWSER_CERTIFICATION=PASS')

if __name__=='__main__': main()
