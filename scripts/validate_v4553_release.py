#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_VERSION="4.55.3"
EXPECTED_REGISTRY="2.4.0"
EXPECTED_ROUTES=1506
EXPECTED_MODULAR=197
EXPECTED_CAPABILITIES=29
EXPECTED_RELEASE_BOUND=40

errors=[]
def ok(label, condition, detail=""):
    if condition: print(f"PASS: {label}")
    else:
        errors.append(label+(f": {detail}" if detail else ""))
        print(f"FAIL: {label}{': '+detail if detail else ''}")

version=(ROOT/"backend/app/version.py").read_text()
ok("v4.55.3 release identity aligned", f'APP_VERSION = "{EXPECTED_VERSION}"' in version and 'Standalone Web Application Foundation & WordPress Decoupling' in version)

registry=json.loads((ROOT/"backend/data/standalone_web_application_registry_v4553.json").read_text())
ok("standalone web registry installed", registry.get("version")==EXPECTED_VERSION and registry.get("wordpress_runtime_dependency") is False)
ok("application and API origins separated", registry.get("application_origin")!=registry.get("api_origin") and registry.get("application_origin")=="https://intelligence.sustainablecatalyst.com")
ok("deep-link country workspaces registered", all(any(r.get("pattern")==p for r in registry["routes"]) for p in ["/economics/:country","/law/:country","/humanitarian/:country","/resources/:country"]))

route_registry=(ROOT/"backend/app/route_registry_v4430.py").read_text()
ok("capability registry 2.4.0 owns standalone web application", '"registry_version": "2.4.0"' in route_registry and 'CapabilitySpec("standalone-web-application"' in route_registry)

web_files=["index.html","config.js","manifest.webmanifest","service-worker.js","Dockerfile","nginx.conf","compose.yml","assets/app.js","assets/api-client.js","assets/context-store.js","assets/router.js","assets/views.js"]
for f in web_files: ok(f"standalone web file exists: {f}",(ROOT/"web"/f).is_file())
web_text="\n".join((ROOT/"web"/f).read_text(errors="ignore") for f in web_files if (ROOT/"web"/f).is_file())
ok("standalone web does not use legacy query-view routing", "/app/?view=" not in web_text)
ok("standalone web API origin configured", "https://site-intelligence-api.sustainablecatalyst.com" in (ROOT/"web/config.js").read_text())
ok("standalone SPA history fallback configured", "try_files $uri $uri/ /index.html" in (ROOT/"web/nginx.conf").read_text())

config=(ROOT/"backend/app/config.py").read_text()
ok("first-party web CORS fallback installed", "self.web_app_url.strip()" in config and "https://intelligence.sustainablecatalyst.com" in config)

php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
ok("WordPress release identity aligned", "Version: 4.55.3" in php and "const VERSION = '4.55.3';" in php)
ok("WordPress demoted to launch bridge", "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php and "STANDALONE_WEB_APP_URL" in php)
block=php[php.index("public function standalone_app_shortcode"):php.index("public function geospatial_map_shortcode")]
ok("primary WordPress app shortcode launches instead of embeds", "<iframe" not in block and "runs independently of WordPress" in block)

backend_helper=(ROOT/"deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_contabo.sh").read_text()
web_helper=(ROOT/"deploy/contabo/upgrade_site_intelligence_web_v4_55_3_contabo.sh").read_text()
ok("backend deploy helper current", 'VERSION="4.55.3"' in backend_helper and 'standalone_web_application_registry_v4553.json' in backend_helper)
ok("web deploy helper current", 'VERSION="4.55.3"' in web_helper and '127.0.0.1:8096' in web_helper)
ok("Caddy standalone host contract exists", "intelligence.sustainablecatalyst.com" in (ROOT/"deploy/contabo/site-intelligence-web-v4553.Caddyfile").read_text())

m=re.search(r'RELEASE_BOUND_POLICIES=\((.*?)\n\)',backend_helper,re.S)
names=re.findall(r'^\s+([A-Za-z0-9_.-]+\.json)\s*$',m.group(1),re.M) if m else []
ok("deployment declares 40 release-bound files", len(names)==EXPECTED_RELEASE_BOUND, str(len(names)))
for name in names:
    path=ROOT/"backend/data"/name
    ok(f"release-bound file exists: {name}",path.is_file())
    if path.is_file():
        try: value=json.loads(path.read_text()).get("version")
        except Exception: value=None
        ok(f"release-bound file aligned: {name}",value==EXPECTED_VERSION,str(value))

# Static inventory values are certified in the focused/selected pytest gate.
test=(ROOT/"backend/tests/test_v4553_standalone_web_application_decoupling.py").read_text()
ok("test inventory assertions current", all(x in test for x in [f'=={EXPECTED_ROUTES}',f'=={EXPECTED_MODULAR}',f'=={EXPECTED_CAPABILITIES}',f'=="{EXPECTED_REGISTRY}"']))

if errors:
    print("V4553_RELEASE_VALIDATION=FAIL")
    for e in errors: print(" -",e)
    sys.exit(1)
print("V4553_RELEASE_VALIDATION=PASS")
