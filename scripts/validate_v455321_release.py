#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re

ROOT=Path(__file__).resolve().parents[1]
VERSION='4.55.3.2.1'
errors=[]

def check(cond,msg):
    print(('PASS: ' if cond else 'FAIL: ')+msg)
    if not cond: errors.append(msg)

version=(ROOT/'backend/app/version.py').read_text()
check(f'APP_VERSION = "{VERSION}"' in version,'release identity 4.55.3.2.1')
check('Runtime Health Truth & Domain Context Repair' in version,'release name')
route_registry=(ROOT/'backend/app/route_registry_v4430.py').read_text()
check('"registry_version": "2.6.1"' in route_registry,'capability registry 2.6.1')

registry=json.loads((ROOT/'backend/data/runtime_health_domain_context_registry_v455321.json').read_text())
check(registry.get('version')==VERSION,'runtime/context registry aligned')
check(registry.get('runtime_health',{}).get('primary_health_path')=='/health','canonical health path declared')
check(registry.get('runtime_health',{}).get('optional_endpoint_failure_state')=='degraded','optional failures degrade rather than offline')
check(registry.get('economics_empty_state',{}).get('fabricated_records') is False,'zero-record state forbids fabrication')

for rel in ['web/app/assets/runtime-v3230.js','backend/public_app/assets/runtime-v3230.js']:
    text=(ROOT/rel).read_text()
    check('primaryService && !primaryService.ok' in text,f'primary health truth in {rel}')
    check('failed >= 3' not in text,f'false-offline threshold removed from {rel}')

for rel in ['web/app/assets/economics-v220.js','backend/public_app/assets/economics-v220.js']:
    text=(ROOT/rel).read_text()
    check('params.get("country") || qs("#countrySelect")?.value' in text,f'global country fallback in {rel}')
    check('no official economics records matched ${domainCountryLabel()}' in text,f'truthful economics empty message in {rel}')

bridge=(ROOT/'web/app/assets/standalone-api-bridge-v45532.js').read_text()
check('const RELEASE="4.55.3.2.1"' in bridge,'standalone bridge release aligned')
check('q.set("geography_code",resolved)' in bridge,'deep-link geography_code propagation')
check('SCSIStandaloneBridgeV455321' in bridge,'corrective bridge alias exported')

config=(ROOT/'web/config.js').read_text()
check('release: "4.55.3.2.1"' in config,'standalone config release aligned')
html=(ROOT/'web/index.html').read_text()
check('data-scsi-release="4.55.3.2.1"' in html,'standalone root release aligned')
check('runtime-v3230.js?v=4.55.3.2.1' in html,'runtime asset cache bust')
check('standalone-api-bridge-v45532.js?v=4.55.3.2.1' in html,'bridge cache bust')
check('try_files $uri $uri/ /index.html' in (ROOT/'web/nginx.conf').read_text(),'SPA/deep-link fallback retained')

helper=(ROOT/'deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_1_contabo.sh').read_text()
block=helper.split('RELEASE_BOUND_POLICIES=(',1)[1].split('\n)',1)[0]
names=[line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith('#')]
check(len(names)==44,'44 release-bound policies declared')
for name in names:
    p=ROOT/'backend/data'/name
    check(p.is_file(),f'release-bound file exists: {name}')
    if p.is_file():
        check(json.loads(p.read_text()).get('version')==VERSION,f'release-bound version aligned: {name}')

web_helper=(ROOT/'deploy/contabo/upgrade_site_intelligence_web_v4_55_3_2_1_contabo.sh').read_text()
check('-o "$TMP/economics.html"' in web_helper,'web deploy verification avoids curl/grep pipefail')
check('primaryService && !primaryService.ok' in web_helper,'web deploy helper verifies health truth repair')

for f in [
    'backend/app/runtime_context_repair_v455321.py',
    'backend/tests/test_v455321_runtime_health_domain_context_repair.py',
    'scripts/browser_certify_v455321.py',
    'deploy/contabo/upgrade_site_intelligence_backend_v4_55_3_2_1_contabo.sh',
    'deploy/contabo/upgrade_site_intelligence_web_v4_55_3_2_1_contabo.sh',
    'docs/V455321_RELEASE_NOTES.md',
    'docs/V455321_RELEASE_CERTIFICATION.md',
    'docs/V455321_INSTALL_AND_VERIFY.md',
]:
    check((ROOT/f).is_file(),f'file exists: {f}')

if errors:
    raise SystemExit('V455321_RELEASE_VALIDATION=FAIL: '+'; '.join(errors))
print('V455321_RELEASE_VALIDATION=PASS')
