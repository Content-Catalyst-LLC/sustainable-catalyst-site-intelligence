#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_VERSION="4.55.3.1"
EXPECTED_REGISTRY="2.5.0"
EXPECTED_ROUTES=1515
EXPECTED_MODULAR=206
EXPECTED_CAPABILITIES=30
EXPECTED_RELEASE_BOUND=41

errors=[]
def ok(label, condition, detail=""):
    if condition:
        print(f"PASS: {label}")
    else:
        errors.append(label+(f": {detail}" if detail else ""))
        print(f"FAIL: {label}{': '+detail if detail else ''}")

version=(ROOT/"backend/app/version.py").read_text()
ok("v4.55.3.1 release identity aligned", f'APP_VERSION = "{EXPECTED_VERSION}"' in version and 'API Reliability & Contract Truth Repair' in version)

contract=json.loads((ROOT/"backend/data/api_reliability_contract_v45531.json").read_text())
ok("API reliability contract installed", contract.get("version")==EXPECTED_VERSION and contract.get("guardrails",{}).get("dependency_failure_reported_ok_true_on_reliable_surface") is False)
ok("no feature/provider expansion in reliability release", contract.get("guardrails",{}).get("new_provider_integrations") is False and contract.get("guardrails",{}).get("new_domain_features") is False)

route_registry=(ROOT/"backend/app/route_registry_v4430.py").read_text()
ok("capability registry 2.5.0 owns API reliability", '"registry_version": "2.5.0"' in route_registry and 'CapabilitySpec("api-reliability"' in route_registry)
ok("legacy capability maturity defaults to migration", 'maturity: str = "migration"' in route_registry)

router=(ROOT/"backend/app/routers/reliability.py").read_text()
for route in [
    '/ready','/public/api-contract-truth','/public/capability-health',
    '/public/reliable/economics/records','/public/reliable/law/records',
    '/public/reliable/science/records','/public/reliable/humanitarian/records',
    '/public/reliable/resources/records','/public/reliable/dossiers/country']:
    ok(f"reliability route declared: {route}", route in router)

system=(ROOT/"backend/app/routers/system.py").read_text()
ok("health is explicitly process-only", '"scope": "process-only"' in system and '"dependency_readiness_asserted": False' in system)

logic=(ROOT/"backend/app/api_reliability_v45531.py").read_text()
ok("reliable surface distinguishes no-records", 'data_state = "records" if count > 0 else "no-records"' in logic)
ok("reliable surface uses 503 for dependency failure", 'status = 503' in logic and 'data_state = "dependency-unavailable"' in logic)
ok("reliable surface supports partial results", 'status = 206' in logic and 'data_state = "partial-records"' in logic)

web=(ROOT/"web/assets/views.js").read_text()
ok("standalone home exposes API data readiness", '/public/capability-health' in web and 'API data readiness' in web)
ok("standalone web port remains 8096", '127.0.0.1:8096:80' in (ROOT/"web/compose.yml").read_text())

php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
ok("WordPress release identity aligned", "Version: 4.55.3.1" in php and "const VERSION = '4.55.3.1';" in php)
ok("WordPress remains launch bridge", "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php)

backend_helper=(ROOT/"deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_1_contabo.sh").read_text()
web_helper=(ROOT/"deploy/contabo/upgrade_site_intelligence_web_v4_55_3_1_contabo.sh").read_text()
ok("backend deploy helper current", 'VERSION="4.55.3.1"' in backend_helper and 'api_reliability_contract_v45531.json' in backend_helper)
ok("backend deploy permits truthful not-ready state", 'readiness_status' in backend_helper and '503)' in backend_helper)
ok("web deploy helper current", 'VERSION="4.55.3.1"' in web_helper and '127.0.0.1:8096' in web_helper)
ok("Caddy contract remains on 8096", 'reverse_proxy 127.0.0.1:8096' in (ROOT/"deploy/contabo/site-intelligence-web-v45531.Caddyfile").read_text())

m=re.search(r'RELEASE_BOUND_POLICIES=\((.*?)\n\)',backend_helper,re.S)
names=re.findall(r'^\s+([A-Za-z0-9_.-]+\.json)\s*$',m.group(1),re.M) if m else []
ok("deployment declares 41 release-bound files", len(names)==EXPECTED_RELEASE_BOUND, str(len(names)))
for name in names:
    path=ROOT/"backend/data"/name
    ok(f"release-bound file exists: {name}",path.is_file())
    if path.is_file():
        try: value=json.loads(path.read_text()).get("version")
        except Exception: value=None
        ok(f"release-bound file aligned: {name}",value==EXPECTED_VERSION,str(value))

focused=(ROOT/"backend/tests/test_v45531_api_reliability_contract_truth.py").read_text()
ok("focused test inventory assertions current", all(x in focused for x in [f'== {EXPECTED_ROUTES}',f'== {EXPECTED_MODULAR}',f'== {EXPECTED_CAPABILITIES}',f'== "{EXPECTED_REGISTRY}"']))

if errors:
    print("V45531_RELEASE_VALIDATION=FAIL")
    for e in errors:
        print(" -",e)
    sys.exit(1)
print("V45531_RELEASE_VALIDATION=PASS")
