#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
def require(condition,message):
    if not condition: errors.append(message)
def text(rel): return (ROOT/rel).read_text(encoding='utf-8')

version=text('backend/app/version.py')
plugin=text('wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php')
js=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js')
css=text('wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css')
require('APP_VERSION = "4.39.2"' in version,'backend APP_VERSION is not 4.39.2')
require('Version: 4.39.2' in plugin and "const VERSION = '4.39.2';" in plugin and 'site-intelligence-v4.39.2' in plugin,'WordPress 4.39.2 identity mismatch')
method=plugin.split('public function site_intelligence_home_shortcode',1)[1].split('private function app_embed_url',1)[0]
for token in ("'Explore the World'","'Earth & Environment'","'Ocean & Space'",'data-scsi-home-summary','scsi-home-summary__metrics','scsi-home-summary__signals','scsi-home-summary__entries'):
    require(token in method,f'homepage preservation marker missing: {token}')
for token in ('const safeItemHtml = function','const renderMinimalFallback = function',"liveAnalyticsEvent('feed_render_failure'",'renderMinimalFallback(data, error);','}, function (error) {'):
    require(token in js,f'Live Intelligence recovery marker missing: {token}')
for token in ('.scsi-home-summary__metrics','.scsi-home-summary__signals','.scsi-home-summary__entries','.scsi-live-intelligence__track'):
    require(token in css,f'CSS contract missing: {token}')
for rel in ('RELEASE_NOTES_SITE_INTELLIGENCE_V4392.md','SITE_INTELLIGENCE_V4392_PRESERVATION_AUDIT.md','SITE_INTELLIGENCE_V4392_INSTALL_AND_TEST.md','SITE_INTELLIGENCE_V4392_TERMINAL_COMMANDS.txt','backend/tests/test_live_intelligence_frontend_recovery_v4392.py','scripts/validate_v4392_surgical_scope.py'):
    require((ROOT/rel).is_file(),f'missing v4.39.2 release file: {rel}')
if errors:
    for e in errors: print('FAIL:',e,file=sys.stderr)
    raise SystemExit(1)
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4392_surgical_scope.py')],check=True)
print('PASS: v4.39.2 Live Intelligence Frontend Recovery release contract')
