#!/usr/bin/env python3
"""Overview-route browser regression for the v4.38.0 Palestine navigation repair."""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from browser_complete_shell_gate_v32362 import document, find_browser


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for v4.38.0 Palestine navigation gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for v4.38.0 Palestine navigation gate.")
        return 2

    html, _ = document("disabled")
    # The complete-shell fixture installs its deterministic fetch shim in <head>.
    # Wrap that shim before application scripts execute and deliberately try to
    # swap Israel/Palestine in the external catalog and overview responses.
    hostile = r"""
<script>
(()=>{
  const prior=window.fetch;
  const hostileCountries={
    ISR:{code:'ISR',iso2:'PS',name:'Palestine',latitude:31.943,longitude:35.2365,income_level:'external-test'},
    PSE:{code:'PSE',iso2:'IL',name:'Israel',latitude:31.3894,longitude:35.0433,income_level:'external-test'}
  };
  window.__v43525FetchLog=[];
  window.fetch=async(input,init)=>{
    const url=new URL(String(input),location.href), path=url.pathname;
    if(path==='/public/countries'){
      const base=await prior(input,init), payload=await base.json();
      const rows=(payload.countries||[]).map(row=>hostileCountries[row.code]?{...row,...hostileCountries[row.code]}:row);
      window.__v43525FetchLog.push('hostile-catalog');
      return new Response(JSON.stringify({...payload,countries:rows}),{status:200,headers:{'Content-Type':'application/json'}});
    }
    let m=path.match(/^\/public\/country-intelligence\/(ISR|PSE)$/);
    if(m){
      const requested=m[1], wrong=requested==='ISR'?'PSE':'ISR';
      window.__v43525FetchLog.push(`${requested}:country-intelligence-as-${wrong}`);
      return new Response(JSON.stringify({ok:true,version:'4.35.25',country_code:wrong,registered_source_count:1,domain_summaries:[]}),{status:200,headers:{'Content-Type':'application/json'}});
    }
    m=path.match(/^\/public\/country\/(ISR|PSE)\/overview$/);
    if(m){
      const requested=m[1], wrong=requested==='ISR'?'PSE':'ISR', h=hostileCountries[requested];
      window.__v43525FetchLog.push(`${requested}:overview-as-${wrong}`);
      return new Response(JSON.stringify({ok:true,version:'4.35.25',country:{code:wrong,iso2:h.iso2,name:h.name,latitude:h.latitude,longitude:h.longitude},map:{default_zoom:8},highlights:[]}),{status:200,headers:{'Content-Type':'application/json'}});
    }
    return prior(input,init);
  };
})();
</script>
"""
    html = html.replace("</head>", hostile + "</head>", 1)

    errors=[]
    results={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu-sandbox"])
        page=browser.new_page(viewport={"width":1280,"height":900})
        page.on("pageerror",lambda error: errors.append(str(error)))
        page.set_content(html,wait_until="domcontentloaded",timeout=45000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')",timeout=20000)
        page.wait_for_function("document.querySelectorAll('#countrySelect option').length >= 170",timeout=20000)
        page.wait_for_function("window.SCSIOverviewMapV3232 && window.SCSICartographicWorkspaceV3230",timeout=10000)
        assert page.evaluate("new URLSearchParams(location.search).get('view')") in (None,"overview")

        def select(code,name):
            page.locator("#countrySelect").select_option(code)
            page.wait_for_function("args => document.querySelector('#countryCode')?.textContent===args.code && document.querySelector('#countryName')?.textContent===args.name",arg={"code":code,"name":name},timeout=10000)
            page.wait_for_timeout(350)
            return page.evaluate("""()=>{const m=window.SCSIOverviewMapV3232?.getMap?.();const c=m?.getCenter?.();return {selected:document.querySelector('#countrySelect')?.value||'',code:document.querySelector('#countryCode')?.textContent||'',name:document.querySelector('#countryName')?.textContent||'',center:c?{lat:Number(c.lat),lng:Number(c.lng)}:null,summary:document.querySelector('#countrySummary')?.textContent||''}}""")

        results["palestine"]=select("PSE","Palestine")
        results["israel"]=select("ISR","Israel")
        results["log"]=page.evaluate("window.__v43525FetchLog")
        browser.close()

    assert not errors,errors
    assert results["palestine"]["selected"]==results["palestine"]["code"]=="PSE",results
    assert results["palestine"]["name"]=="Palestine",results
    assert results["israel"]["selected"]==results["israel"]["code"]=="ISR",results
    assert results["israel"]["name"]=="Israel",results
    # Hostile cross-identity evidence must be blocked rather than replacing the
    # canonical selection. The error text is expected because the fixture is
    # intentionally malicious.
    assert "identity mismatch" in results["palestine"]["summary"].lower(),results
    assert "identity mismatch" in results["israel"]["summary"].lower(),results
    print(json.dumps({"browser":browser_path,"results":results,"errors":errors},indent=2))
    print("PASS: v4.38.0 keeps Palestine and Israel canonical on the Overview selector even when external catalog/overview payloads attempt to swap them.")
    return 0


if __name__=="__main__":
    try: status=int(main())
    except BaseException:
        traceback.print_exc();status=1
    try: sys.stdout.flush();sys.stderr.flush()
    finally: os._exit(status)
