#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "4.55.3.1.1"
EXPECTED_REGISTRY = "2.5.1"
EXPECTED_ROUTES = 1515
EXPECTED_MODULAR = 206
EXPECTED_CAPABILITIES = 30
EXPECTED_RELEASE_BOUND = 42

errors=[]
def check(label, condition, detail=""):
    if condition:
        print(f"PASS: {label}")
    else:
        errors.append(label + (f": {detail}" if detail else ""))
        print(f"FAIL: {label}{': '+detail if detail else ''}")

version=(ROOT/'backend/app/version.py').read_text()
check('v4.55.3.1.1 release identity aligned', f'APP_VERSION = "{EXPECTED_VERSION}"' in version and 'Live Probe Consistency & Domain Failure Normalization' in version)

logic=(ROOT/'backend/app/api_reliability_v455311.py').read_text()
check('shared canonical probe implementation installed', 'def probe_capability(' in logic and 'CANONICAL_CAPABILITIES' in logic)
check('science geography TypeError path removed', 'context_mode": "metadata-query"' in logic and 'build_science_records(settings, query=science_query' in logic)
check('expected exceptions normalized', 'def _exception_payload' in logic and '"normalized": True' in logic)
check('partial-live transport semantics corrected', '"partial-no-records"' in logic and 'status, ok = 206, True' in logic)
check('readiness includes domain operability', '"platform_ready"' in logic and '"domain_ready"' in logic and 'build_capability_health(settings, probe=True' in logic)
check('country identity canonicalization installed', 'canonical_country' in logic and '"iso3"' in logic and '"iso2"' in logic)

router=(ROOT/'backend/app/routers/reliability.py').read_text()
check('router delegates to shared probe', 'probe_capability' in router and 'def _respond' in router)
check('science reliable route accepts geography context safely', 'reliable_science_records' in router and 'country=geography_code' in router)

registry=(ROOT/'backend/data/live_probe_consistency_registry_v455311.json')
check('live probe consistency registry exists', registry.is_file())
if registry.is_file():
    data=json.loads(registry.read_text())
    check('live probe registry version aligned', data.get('version')==EXPECTED_VERSION, str(data.get('version')))
    check('live probe registry forbids raw reliable-route 500s', data.get('guardrails',{}).get('raw_unhandled_500_allowed_on_reliable_routes') is False)
    check('release adds no providers/features', data.get('guardrails',{}).get('new_provider_integrations') is False and data.get('guardrails',{}).get('new_domain_features') is False)

route_registry=(ROOT/'backend/app/route_registry_v4430.py').read_text()
check('capability registry 2.5.1', f'"registry_version": "{EXPECTED_REGISTRY}"' in route_registry)
check('API reliability capability remains production', 'CapabilitySpec("api-reliability"' in route_registry and '"production")' in route_registry)

views=(ROOT/'web/assets/views.js').read_text()
for route in ['/public/reliable/economics/records','/public/reliable/law/records','/public/reliable/science/records','/public/reliable/humanitarian/records','/public/reliable/resources/records','/public/reliable/dossiers/country']:
    check(f'standalone view uses reliable route {route}', route in views)
check('standalone home requests live capability probe', 'probe:true' in views)
check('standalone web port remains 8096', '127.0.0.1:8096:80' in (ROOT/'web/compose.yml').read_text())

php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
check('WordPress identity aligned', 'Version: 4.55.3.1.1' in php and "const VERSION = '4.55.3.1.1';" in php)
check('WordPress remains launch bridge', "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php)

helper=(ROOT/'deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_1_1_contabo.sh').read_text()
check('backend helper current', 'VERSION="4.55.3.1.1"' in helper and 'live_probe_consistency_registry_v455311.json' in helper)
check('backend helper fixes docker heredoc stdin', 'docker exec -i "$CONTAINER" python -' in helper)
check('backend helper accepts truthful readiness 503', '503)' in helper and 'domain-degraded' in helper)
web_helper=(ROOT/'deploy/contabo/upgrade_site_intelligence_web_v4_55_3_1_1_contabo.sh').read_text()
check('web helper current', 'VERSION="4.55.3.1.1"' in web_helper and '127.0.0.1:8096' in web_helper)
check('Caddy remains 8096', 'reverse_proxy 127.0.0.1:8096' in (ROOT/'deploy/contabo/site-intelligence-web-v455311.Caddyfile').read_text())

m=re.search(r'RELEASE_BOUND_POLICIES=\((.*?)\n\)', helper, re.S)
names=re.findall(r'^\s+([A-Za-z0-9_.-]+\.json)\s*$',m.group(1),re.M) if m else []
check('deployment declares 42 release-bound files', len(names)==EXPECTED_RELEASE_BOUND, str(len(names)))
for name in names:
    path=ROOT/'backend/data'/name
    check(f'release-bound file exists: {name}', path.is_file())
    if path.is_file():
        try: value=json.loads(path.read_text()).get('version')
        except Exception: value=None
        check(f'release-bound file aligned: {name}', value==EXPECTED_VERSION, str(value))

focused=(ROOT/'backend/tests/test_v455311_live_probe_consistency_failure_normalization.py').read_text()
check('focused test inventory current', all(x in focused for x in [f'== {EXPECTED_ROUTES}',f'== {EXPECTED_MODULAR}',f'== {EXPECTED_CAPABILITIES}',f'== "{EXPECTED_REGISTRY}"']))

if errors:
    print('V455311_RELEASE_VALIDATION=FAIL')
    for e in errors: print(' -',e)
    sys.exit(1)
print('V455311_RELEASE_VALIDATION=PASS')
