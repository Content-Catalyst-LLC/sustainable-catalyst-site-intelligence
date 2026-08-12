#!/usr/bin/env python3
"""Browser regression for ISR/PSE country-selector identity isolation (v4.35.23)."""
from __future__ import annotations

import json
import os
import traceback
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import app.live_country_intelligence as live_country
from browser_complete_shell_gate_v32362 import document, find_browser


def main() -> int:
    browser_path = find_browser()
    if not browser_path:
        print("ERROR: Chromium or Chrome is required for v4.35.23 country identity routing gate.")
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is required for v4.35.23 country identity routing gate.")
        return 2

    # Keep the complete-shell fixture first-party and deterministic. Country identity
    # must not depend on World Bank catalog availability during this browser gate.
    live_country._catalog_from_world_bank = lambda: {}
    live_country._COUNTRY_CATALOG_CACHE = live_country._normalized_static_catalog()
    live_country._COUNTRY_CATALOG_FETCHED_AT = "2026-08-12T00:00:00Z"
    live_country._COUNTRY_CATALOG_STATE = "fallback-catalog"

    results = {}
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=browser_path, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-sandbox"])
        html, _ = document("disabled")
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(html, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_function("document.querySelector('#app')?.classList.contains('app-ready')", timeout=20000)
        page.wait_for_function("document.querySelectorAll('#countrySelect option').length >= 170", timeout=20000)

        page.evaluate(
            r"""()=>{
              const prior=window.fetch;
              const identities={
                KEN:{code:'KEN',name:'Kenya',iso2:'KE',region:'Sub-Saharan Africa',capital:'Nairobi',latitude:0.0236,longitude:37.9062},
                ISR:{code:'ISR',name:'Israel',iso2:'IL',region:'Middle East, North Africa, Afghanistan & Pakistan',capital:'Jerusalem',latitude:31.3894,longitude:35.0433},
                PSE:{code:'PSE',name:'Palestine',iso2:'PS',region:'Middle East, North Africa, Afghanistan & Pakistan',capital:'Ramallah',latitude:31.943,longitude:35.2365}
              };
              window.__identityFetchLog=[];
              window.fetch=async(input,init)=>{
                const url=new URL(String(input),location.href),path=url.pathname;
                const m=path.match(/^\/public\/country\/(KEN|ISR|PSE)\/(overview|trends|linked-records|evidence-reconciliation|knowledge-context|data-federation)$/);
                if(m){
                  const code=m[1],kind=m[2],country=identities[code];window.__identityFetchLog.push(`${code}:${kind}`);
                  let body={ok:true,version:'4.35.23',country};
                  if(kind==='overview')body={...body,headline:`${country.name} — Global Country Intelligence`,summary:`${country.name} country identity regression fixture.`,evidence_summary:'identity fixture',map:{latitude:country.latitude,longitude:country.longitude,default_zoom:5},highlights:[],missing_indicators:[]};
                  else if(kind==='trends')body={...body,trends:[]};
                  else if(kind==='linked-records')body={...body,records:[]};
                  else if(kind==='evidence-reconciliation')body={...body,summary:{},indicators:[]};
                  else if(kind==='knowledge-context')body={...body,entity:{label:country.name},wikipedia:{},attention:{days:30,total:0},media:[]};
                  else if(kind==='data-federation')body={...body,source_precedence:[]};
                  return new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}});
                }
                return prior(input,init);
              };
            }"""
        )

        page.evaluate("document.querySelector('.nav-item[data-route=\"country\"]')?.click()")
        page.wait_for_function("!document.querySelector('#globalCountryExplorer').hidden", timeout=10000)

        def select_and_snapshot(code: str, name: str) -> dict[str, str]:
            page.locator("#countrySelect").select_option(code)
            page.wait_for_function("expected => document.querySelector('#countryIdentityCode')?.textContent === expected", arg=code, timeout=10000)
            page.wait_for_function("expected => (document.querySelector('#countryIdentityName')?.textContent || '') === expected", arg=name, timeout=10000)
            return page.evaluate("""()=>({selected:document.querySelector('#countrySelect')?.value||'',code:document.querySelector('#countryIdentityCode')?.textContent||'',name:document.querySelector('#countryIdentityName')?.textContent||'',title:document.querySelector('#globalCountryTitle')?.textContent||''})""")

        results["palestine"] = select_and_snapshot("PSE", "Palestine")
        results["israel"] = select_and_snapshot("ISR", "Israel")

        page.evaluate("""()=>{const s=document.querySelector('#countrySelect');s.value='PSE';s.dispatchEvent(new Event('change',{bubbles:true}));s.value='ISR';s.dispatchEvent(new Event('change',{bubbles:true}))}""")
        page.wait_for_function("document.querySelector('#countryIdentityCode')?.textContent === 'ISR' && document.querySelector('#countryIdentityName')?.textContent === 'Israel'", timeout=10000)
        results["rapid_to_israel"] = page.evaluate("""()=>({selected:document.querySelector('#countrySelect')?.value,code:document.querySelector('#countryIdentityCode')?.textContent,name:document.querySelector('#countryIdentityName')?.textContent})""")

        page.evaluate("""()=>{const s=document.querySelector('#countrySelect');s.value='ISR';s.dispatchEvent(new Event('change',{bubbles:true}));s.value='PSE';s.dispatchEvent(new Event('change',{bubbles:true}))}""")
        page.wait_for_function("document.querySelector('#countryIdentityCode')?.textContent === 'PSE' && document.querySelector('#countryIdentityName')?.textContent === 'Palestine'", timeout=10000)
        results["rapid_to_palestine"] = page.evaluate("""()=>({selected:document.querySelector('#countrySelect')?.value,code:document.querySelector('#countryIdentityCode')?.textContent,name:document.querySelector('#countryIdentityName')?.textContent})""")
        results["fetch_log"] = page.evaluate("window.__identityFetchLog")
        browser.close()

    assert not errors, errors
    assert results["palestine"]["selected"] == results["palestine"]["code"] == "PSE", results
    assert results["palestine"]["name"] == "Palestine" and "Palestine" in results["palestine"]["title"], results
    assert results["israel"]["selected"] == results["israel"]["code"] == "ISR", results
    assert results["israel"]["name"] == "Israel" and "Israel" in results["israel"]["title"], results
    assert results["rapid_to_israel"] == {"selected":"ISR","code":"ISR","name":"Israel"}, results
    assert results["rapid_to_palestine"] == {"selected":"PSE","code":"PSE","name":"Palestine"}, results
    print(json.dumps({"browser": browser_path, "results": results, "errors": errors}, indent=2))
    print("PASS: v4.35.23 keeps Israel (ISR) and Palestine (PSE) isolated across direct and rapid country-selector changes.")
    return 0


if __name__ == "__main__":
    try:
        status = int(main())
    except BaseException:
        traceback.print_exc()
        status = 1
    try:
        import sys
        sys.stdout.flush(); sys.stderr.flush()
    finally:
        os._exit(status)
