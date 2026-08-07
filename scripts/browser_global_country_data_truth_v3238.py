#!/usr/bin/env python3
from pathlib import Path
import json,sys,os,shutil
try: from playwright.sync_api import sync_playwright
except Exception: print('ERROR: Playwright unavailable.',file=sys.stderr); raise SystemExit(2)
def browser_path():
 candidates=[os.getenv('SC_SI_CHROMIUM',''),shutil.which('chromium') or '',shutil.which('google-chrome') or '',shutil.which('google-chrome-stable') or '','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Chromium.app/Contents/MacOS/Chromium']
 return next((x for x in candidates if x and Path(x).is_file() and os.access(x,os.X_OK)),None)
BROWSER=browser_path()
if not BROWSER: print('ERROR: Chromium or Chrome is required.',file=sys.stderr); raise SystemExit(2)
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'backend/public_app/assets/data-truth-v32371.js').read_text()
CSS=(ROOT/'backend/public_app/assets/data-truth-v32371.css').read_text()
country={"ok":True,"version":"3.28.0","country":{"code":"BRA","name":"Brazil"},"summary":{"available":0,"partial":1,"historical_only":0,"no_recent_records":0,"unknown":5,"unavailable":0,"not_applicable":2},"sources":[{"feed_id":"world_bank","label":"World Bank Indicators","publisher":"World Bank","coverage_state":"unknown","eligibility":"eligible","evidence_level":"contract_only","country_resolution":"national_indicator","operational_state":"demonstration","reason":"Indicator availability varies."}],"indicators":[{"indicator_id":"SP.POP.TOTL","label":"Population","domain":"Population","coverage_state":"unknown","unit":"people","value":None,"observation_year":None}]}
matrix={"ok":True,"version":"3.28.0","country_count":2,"source_count":1,"columns":[{"feed_id":"world_bank","label":"World Bank Indicators","domain":"indicators"}],"rows":[{"country":{"code":"BRA","name":"Brazil"},"summary":{},"cells":[{"feed_id":"world_bank","coverage_state":"unknown","eligibility":"eligible","evidence_level":"contract_only","reason":"Not observed"}]},{"country":{"code":"KEN","name":"Kenya"},"summary":{},"cells":[{"feed_id":"world_bank","coverage_state":"historical_only","eligibility":"eligible","evidence_level":"packaged_snapshot","reason":"Dated snapshot"}]}]}
sources={"ok":True,"version":"3.28.0","sources":[{"label":"World Bank Indicators","publisher":"World Bank","data_state":{"presentation":"demonstration","reason":"No successful production retrieval."},"coverage":{"geographic":"Global"},"retrieval":{}}]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content('<!doctype html><style>'+CSS+'</style><div id="app" data-scsi-release="3.28.0"><header><div class="topbar-controls"><select id="countrySelect"><option value="BRA">Brazil</option><option value="KEN">Kenya</option></select></div></header></div>')
 page.evaluate("payloads=>{window.fetch=async url=>({ok:true,json:async()=>url.includes('coverage-matrix')?payloads.matrix:url.endsWith('/public/data-truth')?payloads.sources:payloads.country})}",{"country":country,"matrix":matrix,"sources":sources})
 page.add_script_tag(content=JS);page.click('#dataTruthToggle');page.wait_for_selector('text=Brazil (BRA)');country_ready=page.locator('text=Brazil (BRA)').count()>0;page.click('[data-truth-view="matrix"]');page.wait_for_selector('.scsi-coverage-matrix [data-country-search*="kenya"]');page.fill('#dataTruthMatrixFilter','Brazil');hidden=page.locator('[data-country-search]').nth(1).is_hidden();result={"errors":errors,"country_ready":country_ready,"matrix_ready":page.locator('.scsi-coverage-matrix').count()==1,"filter_hides":hidden,"api":page.evaluate('window.SCSIDataTruthV32371.version')};b.close()
print(json.dumps(result,indent=2));assert not errors and result['country_ready'] and result['matrix_ready'] and result['filter_hides'] and result['api']=='3.28.0';print('PASS: v3.28.0 country truth and coverage matrix rendered without browser errors.')
