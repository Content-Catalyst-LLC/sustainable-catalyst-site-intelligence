from __future__ import annotations
from pathlib import Path
import hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
BASELINE=json.loads((ROOT/'docs/V4392_PROTECTED_V4390_BASELINE.json').read_text(encoding='utf-8'))

def sha(data: bytes)->str: return hashlib.sha256(data).hexdigest()
def fail(msg): print('FAIL - '+msg); raise SystemExit(1)
def ok(msg): print('PASS - '+msg)

# 1) All non-target runtime files are byte-identical to v4.39.0.
for rel,expected in BASELINE['protected_files'].items():
    p=ROOT/rel
    if not p.is_file(): fail('protected file missing: '+rel)
    if sha(p.read_bytes())!=expected: fail('protected file changed: '+rel)
ok(f"{len(BASELINE['protected_files'])} non-target runtime files are byte-identical to v4.39.0")

# 2) Governed policy files may change only their top-level version string.
for rel in BASELINE['policy_version_only_files']:
    p=ROOT/rel
    text=p.read_text(encoding='utf-8')
    try: payload=json.loads(text)
    except Exception as exc: fail(f'invalid policy JSON {rel}: {exc}')
    if not isinstance(payload,dict) or payload.get('version')!='4.39.2': fail('policy version is not 4.39.2: '+rel)
    normalized=text.replace('"version": "4.39.2"','"version": "4.39.0"',1)
    if text.count('\"version\": \"4.39.2\"') < 1: fail('policy version token missing: '+rel)
    if normalized == text: fail('policy version normalization failed: '+rel)
    expected=BASELINE['policy_baseline_sha256'][rel]
    if sha(normalized.encode('utf-8'))!=expected: fail('policy changed beyond top-level version metadata: '+rel)
ok(f"{len(BASELINE['policy_version_only_files'])} governed policy files changed only release version metadata")

# 3) Backend version.py differs only in APP_VERSION.
vp=ROOT/'backend/app/version.py'; vt=vp.read_text(encoding='utf-8')
if 'APP_VERSION = "4.39.2"' not in vt: fail('backend APP_VERSION is not 4.39.2')
vnorm=vt.replace('APP_VERSION = "4.39.2"','APP_VERSION = "4.39.0"',1)
if sha(vnorm.encode())!=BASELINE['baseline_backend_version_sha256']: fail('backend version.py changed beyond APP_VERSION')
if 'EXPECTED_WORDPRESS_PLUGIN_VERSION = APP_VERSION' not in vt: fail('expected plugin version no longer derives from APP_VERSION')
ok('backend change is limited to central APP_VERSION identity')

# 4) WordPress bootstrap differs only in release identity.
php_path=ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php'
php=php_path.read_text(encoding='utf-8')
for marker in [' * Version: 4.39.2',"const VERSION = '4.39.2';","const RELEASE_ID = 'site-intelligence-v4.39.2';"]:
    if marker not in php: fail('missing WordPress identity marker: '+marker)
pnorm=php.replace(' * Version: 4.39.2',' * Version: 4.39.0',1).replace("const VERSION = '4.39.2';","const VERSION = '4.39.0';",1).replace("const RELEASE_ID = 'site-intelligence-v4.39.2';","const RELEASE_ID = 'site-intelligence-v4.39.0';",1)
if sha(pnorm.encode())!=BASELINE['baseline_plugin_php_sha256']: fail('WordPress bootstrap changed beyond version/release identity')
ok('WordPress bootstrap differs only in 4.39.2 identity')

# 5) Approved homepage structure remains intact.
m=re.search(r'public function site_intelligence_home_shortcode\(\$atts = \[\]\) \{(.*?)\n    private function app_embed_url',php,re.S)
if not m: fail('Site Intelligence homepage shortcode not found')
home=m.group(1)
for marker in ["'Explore the World'","'Earth & Environment'","'Ocean & Space'",'data-scsi-home-summary','scsi-home-summary__metrics','scsi-home-summary__signals','scsi-home-summary__entries']:
    if marker not in home: fail('approved homepage marker missing: '+marker)
ok('approved Site Intelligence homepage structure retained')

# 6) JS change cannot escape the Live Intelligence function.
js=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js').read_text(encoding='utf-8')
try:
    start=js.index('  function setupLiveIntelligence() {'); end=js.index('  function setupLiveIntelligenceSubscriptions()',start)
except ValueError as exc: fail('Live Intelligence boundary missing: '+str(exc))
b=BASELINE['live_intelligence_boundary']
if sha(js[:start].encode())!=b['prefix_sha256']: fail('JavaScript changed before setupLiveIntelligence()')
if sha(js[end:].encode())!=b['suffix_sha256']: fail('JavaScript changed after setupLiveIntelligence()')
fn=js[start:end]
for marker in ['const safeItemHtml = function','const renderMinimalFallback = function',"liveAnalyticsEvent('feed_render_failure'",'renderMinimalFallback(data, error);','}, function (error) {','Site Intelligence Live Intelligence fetch failed.']:
    if marker not in fn: fail('Live Intelligence repair marker missing: '+marker)
ok('Live Intelligence recovery is isolated to setupLiveIntelligence()')

print('RESULT: PASS - Site Intelligence v4.39.2 surgical preservation gate')
