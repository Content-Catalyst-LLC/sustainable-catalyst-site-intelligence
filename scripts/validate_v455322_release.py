#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
VERSION="4.55.3.2.2"
errors=[]
def check(cond,msg):
    print(("PASS: " if cond else "FAIL: ")+msg)
    if not cond: errors.append(msg)
version=(ROOT/"backend/app/version.py").read_text()
check(f'APP_VERSION = "{VERSION}"' in version,"release identity 4.55.3.2.2")
check("Browser API Transport & CORS Repair" in version,"release name")
route_registry=(ROOT/"backend/app/route_registry_v4430.py").read_text()
check('"registry_version": "2.6.2"' in route_registry,"capability registry 2.6.2")
registry=json.loads((ROOT/"backend/data/browser_api_transport_registry_v455322.json").read_text())
check(registry.get("version")==VERSION,"browser API transport registry aligned")
check(registry.get("primary_health_path")=="/health","canonical browser health path declared")
check(registry.get("runtime_transport",{}).get("ordinary_public_gets_require_custom_header") is False,"ordinary health GET is preflight-light")
main=(ROOT/"backend/app/main.py").read_text()
check('"X-SCSI-Runtime-Diagnostic"' in main,"FastAPI CORS allows runtime diagnostic header")
for rel in ["web/app/assets/runtime-v3230.js","backend/public_app/assets/runtime-v3230.js"]:
    text=(ROOT/rel).read_text()
    check('headers: { Accept: "application/json" }' in text,f"public runtime GET is simple-header transport: {rel}")
    check('"X-SCSI-Runtime-Diagnostic": VERSION' not in text,f"runtime custom-header dependency removed: {rel}")
    check('primaryService && !primaryService.ok' in text,f"strict offline classification retained: {rel}")
config=(ROOT/"web/config.js").read_text()
check('release: "4.55.3.2.2"' in config,"standalone config aligned")
html=(ROOT/"web/index.html").read_text()
check('data-scsi-release="4.55.3.2.2"' in html,"standalone root aligned")
check('runtime-v3230.js?v=4.55.3.2.2' in html,"runtime cache bust")
helper=(ROOT/"deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_2_contabo.sh").read_text()
block=helper.split("RELEASE_BOUND_POLICIES=(",1)[1].split("\n)",1)[0]
names=[line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
check(len(names)==45,"45 release-bound policies declared")
for name in names:
    p=ROOT/"backend/data"/name
    check(p.is_file(),f"release-bound file exists: {name}")
    if p.is_file(): check(json.loads(p.read_text()).get("version")==VERSION,f"release-bound version aligned: {name}")
for f in ["backend/app/browser_api_transport_v455322.py","backend/tests/test_v455322_browser_api_transport_cors_repair.py","scripts/browser_certify_v455322.py","docs/V455322_RELEASE_NOTES.md","docs/V455322_RELEASE_CERTIFICATION.md","docs/V455322_INSTALL_AND_VERIFY.md"]:
    check((ROOT/f).is_file(),f"file exists: {f}")
if errors: raise SystemExit("V455322_RELEASE_VALIDATION=FAIL: "+"; ".join(errors))
print("V455322_RELEASE_VALIDATION=PASS")
