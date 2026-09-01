#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)
def text(rel): return (ROOT/rel).read_text(encoding='utf-8')
version=text('backend/app/version.py')
plugin=text('wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php')
main=text('backend/app/main.py')
space=text('backend/app/live_space_observation_v4380.py')
health=text('backend/app/release_health_v4380.py')
space_js=text('backend/public_app/assets/live-space-observation-v4380.js')
space_wp=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/live-space-observation-v4380.js')
iframe_css=text('backend/public_app/assets/iframe-navigation-v4380.css')
iframe_wp=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/iframe-navigation-v4380.css')
html=text('backend/public_app/index.html')
html_wp=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/index.html')
sw=text('backend/public_app/service-worker.js')
readme=text('README.md')
req('APP_VERSION = "4.39.0"' in version,'backend APP_VERSION is not 4.39.0')
req('Version: 4.39.0' in plugin and 'site-intelligence-v4.39.0' in plugin,'WordPress release identity mismatch')
for endpoint in ('/public/space-observation/providers','/public/space-observation/readiness','/public/space-observation/search'):
    req(endpoint in main,f'missing public endpoint {endpoint}')
for token in ('USGS_STAC','MAST_INVOKE','HORIZONS','EXO_TAP','BREAKTHROUGH','credential_free_core_space','network_free_readiness'):
    req(token in space,f'live Space control plane missing {token}')
for token in ('deployment-verification-live-space-observation-v4380','live_space_observation_ready','space_credential_free_core_ready','space_readiness_network_free'):
    req(token in health,f'v4.38 release health missing {token}')
req('const VERSION="4.39.0"' in space_js,'live Space browser controller not 4.39.0')
req('/public/space-observation/search' in space_js and '/public/space-observation/providers' in space_js,'live Space browser APIs missing')
req(space_js==space_wp,'WordPress live Space JS mirror differs from backend')
req(iframe_css==iframe_wp,'WordPress iframe CSS mirror differs from backend')
for token in ('data-ocean-entry="hub"','data-space-entry="hub"','liveSpaceObservation','/app/assets/live-space-observation-v4380.js?v=4.39.0','/app/assets/iframe-navigation-v4380.css?v=4.39.0','/app/assets/app.js?v=4.39.0'):
    req(token in html,f'public app missing {token}')
req(html==html_wp,'WordPress index mirror differs from backend')
req('const RELEASE="4.39.0"' in sw and 'const REPAIR="v4380"' in sw,'service worker is not on v4.38 cache lineage')
req('Live Space Observation, Planetary Imagery & Archive Retrieval + Iframe Navigation Repair' in readme,'README current release label missing')
for rel in ('backend/tests/test_live_space_observation_v4380.py','scripts/browser_space_iframe_v4380.py','backend/app/live_space_observation_v4380.py','backend/app/release_health_v4380.py','backend/public_app/assets/live-space-observation-v4380.js','backend/public_app/assets/live-space-observation-v4380.css','backend/public_app/assets/iframe-navigation-v4380.css','RELEASE_NOTES_SITE_INTELLIGENCE_V4380.md','SITE_INTELLIGENCE_V4380_LIVE_SPACE_IFRAME_AUDIT.md','SITE_INTELLIGENCE_V4380_INSTALL_AND_TEST.md','SITE_INTELLIGENCE_V4380_TERMINAL_COMMANDS.txt','SITE_INTELLIGENCE_V4380_BUILD_VALIDATION.txt'):
    req((ROOT/rel).is_file(),f'missing release file {rel}')
if errors:
    for e in errors: print('FAIL:',e,file=sys.stderr)
    raise SystemExit(1)
print('PASS: v4.39.0 Live Space Observation + iframe navigation release contract')
