#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)
def text(rel): return (ROOT/rel).read_text(encoding='utf-8')
version=text('backend/app/version.py')
plugin=text('wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php')
main=text('backend/app/main.py')
live=text('backend/app/live_underwater_media_v4370.py')
uw=text('backend/public_app/assets/underwater-observation-v4800.js')
uw_wp=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/underwater-observation-v4800.js')
html=text('backend/public_app/index.html')
sw=text('backend/public_app/service-worker.js')
readme=text('README.md')
req('APP_VERSION = "4.39.0"' in version,'backend APP_VERSION is not 4.39.0')
req('Version: 4.39.0' in plugin and "site-intelligence-v4.39.0" in plugin,'WordPress release identity mismatch')
for endpoint in ('/public/underwater-media/providers','/public/underwater-media/readiness','/public/underwater-media/search','/public/underwater-media/onc/file'):
    req(endpoint in main,f'missing public endpoint {endpoint}')
for token in ('FATHOMNET_API','NOAA_VIDEO_PORTAL','ONC_API','SC_SI_ONC_API_TOKEN','three_provider_lanes_registered','onc_missing_credential_non_blocking'):
    req(token in live,f'live underwater control plane missing {token}')
req('const VERSION="4.39.0"' in uw,'underwater browser controller not 4.39.0')
req('/public/underwater-media/search' in uw and '/public/underwater-media/providers' in uw,'underwater browser live APIs missing')
req('value="0"' not in uw,'underwater UI contains a fake zero default')
req(uw==uw_wp,'WordPress underwater JS mirror differs from backend')
req('data-ocean-entry="hub"' in html and 'data-space-entry="hub"' in html,'Ocean/Space featured controls not preserved')
req('/app/assets/app.js?v=4.39.0' in html,'current router cache lineage is not 4.39.0')
req('const REPAIR="v4370"' in sw,'service worker is not on v4370 cache lineage')
req('Live Underwater Media Discovery, Imagery & Video Retrieval' in readme,'README current release label missing')
for rel in ('RELEASE_NOTES_SITE_INTELLIGENCE_V4370.md','SITE_INTELLIGENCE_V4370_LIVE_UNDERWATER_MEDIA_AUDIT.md','SITE_INTELLIGENCE_V4370_INSTALL_AND_TEST.md','SITE_INTELLIGENCE_V4370_TERMINAL_COMMANDS.txt'):
    req((ROOT/rel).is_file(),f'missing release document {rel}')
if errors:
    for e in errors: print('FAIL:',e,file=sys.stderr)
    raise SystemExit(1)
print('PASS: v4.39.0 Live Underwater Media Discovery release contract')
