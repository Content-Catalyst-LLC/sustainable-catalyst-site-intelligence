#!/usr/bin/env python3
"""Network-independent Chromium smoke test for v3.23.6.1 analytical workflow presentation."""
from __future__ import annotations
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/"backend/public_app/assets/analytical-workspaces-v3234.js"
CSS=ROOT/"backend/public_app/assets/analytical-workspaces-v3234.css"

def main()->int:
 chromium=shutil.which("chromium") or shutil.which("chromium-browser")
 if not chromium:
  print("SKIP: Chromium is unavailable.");return 0
 try:
  from playwright.sync_api import sync_playwright
 except ImportError:
  print("SKIP: Playwright is unavailable.");return 0
 workflows=[]
 for i,(wid,label,route) in enumerate((("global_conditions","Global Conditions","global"),("country_intelligence","Country Intelligence","country"),("compare","Country and Indicator Comparison","compare"),("spatial_evidence","Spatial Evidence","spatial"),("earth_observation","Earth Observation","earth"))):
  workflows.append({"workflow_id":wid,"label":label,"route":route,"status":"operational","purpose":f"Complete {label} workflow.","stages":["load","analyze","review"],"outputs":["result","sources"],"export_endpoint":"/export","empty_state":"Visible empty state.","degraded_state":"Visible degraded state.","deep_link":f"/app/?view={route}"})
 payload={"ok":True,"version":"3.23.6.1","workflow_count":5,"summary":{"operational":5,"limited":0,"unavailable":0},"workflows":workflows,"completion_gate":{"principle":"Non-live records cannot claim live status."}}
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=chromium,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu-sandbox"])
  page=browser.new_page(viewport={"width":1280,"height":820})
  page.on("console",lambda m:errors.append(f"console:{m.type}:{m.text}") if m.type=="error" else None)
  page.on("pageerror",lambda e:errors.append(f"pageerror:{e}"))
  page.set_content('<!doctype html><html><body><div id="app" data-scsi-release="3.23.6.1"><header class="topbar"><div class="topbar-controls"></div></header><nav><button class="nav-item" data-route="global">Global</button><button class="nav-item" data-route="country">Country</button><button class="nav-item" data-route="compare">Compare</button><button class="nav-item" data-route="spatial">Spatial</button><button class="nav-item" data-route="earth">Earth</button></nav></div></body></html>')
  page.add_style_tag(content=CSS.read_text())
  page.evaluate("payload=>{window.fetch=async()=>({ok:true,json:async()=>payload});window.__opened=[];document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>window.__opened.push(b.dataset.route)));}",payload)
  page.add_script_tag(content=JS.read_text());page.wait_for_timeout(250);page.click('#analyticalWorkflowToggle')
  result=page.evaluate("() => ({visible:!document.querySelector('#analyticalWorkflowPanel').hidden,cards:document.querySelectorAll('.scsi-workflow-card').length,summary:document.querySelectorAll('.scsi-workflow-summary div').length,links:document.querySelectorAll('.scsi-workflow-card a').length,states:document.body.innerText.includes('Ready, empty, degraded, unavailable'),hostGuard:window.SCSIAnalyticalWorkspacesV3234.insideApp()})")
  page.click('.scsi-workflow-card[data-workflow-id="global_conditions"] [data-open-route]');page.wait_for_timeout(50)
  opened=page.evaluate("window.__opened")
  browser.close()
 assert result=={"visible":True,"cards":5,"summary":3,"links":5,"states":True,"hostGuard":True},result
 assert opened==["global"],opened
 assert not errors,errors
 print(json.dumps({**result,"opened":opened},indent=2));print("PASS: v3.23.6.1 rendered five bounded analytical workflows with route actions and no host leakage.");return 0
if __name__=="__main__":raise SystemExit(main())
