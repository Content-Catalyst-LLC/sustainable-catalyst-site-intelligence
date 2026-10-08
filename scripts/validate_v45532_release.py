#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def check(cond,msg):
    print(('PASS: ' if cond else 'FAIL: ')+msg)
    if not cond: errors.append(msg)
version=(ROOT/'backend/app/version.py').read_text()
check('APP_VERSION = "4.55.3.2"' in version,'release identity 4.55.3.2')
check('Standalone Functional Parity Recovery' in version,'release name')
reg=json.loads((ROOT/'backend/data/standalone_functional_parity_registry_v45532.json').read_text())
check(reg.get('version')=='4.55.3.2','functional parity registry aligned')
check(len(reg.get('required_workspaces',[]))>=30,'30+ migrated workspaces declared')
html=(ROOT/'web/index.html').read_text()
check('id="primaryNavigation"' in html and 'id="economicsStudio"' in html,'functional public app promoted to standalone root')
check('standalone-api-bridge-v45532.js' in html,'standalone API bridge injected')
bridge=(ROOT/'web/app/assets/standalone-api-bridge-v45532.js').read_text()
for target in ['/public/reliable/economics/records','/public/reliable/law/records','/public/reliable/science/records','/public/reliable/humanitarian/records','/public/reliable/resources/records','/public/reliable/dossiers/country']:
    check(target in bridge,f'reliable route bridged: {target}')
check('try_files $uri $uri/ /index.html' in (ROOT/'web/nginx.conf').read_text(),'SPA/deep-link fallback')
check(len(list((ROOT/'web/app/assets').glob('*')))>=190,'legacy functional asset surface migrated')
for f in ['backend/app/standalone_functional_parity_v45532.py','backend/app/routers/functional_parity.py','backend/tests/test_v45532_standalone_functional_parity_recovery.py','scripts/browser_certify_v45532.py']:
    check((ROOT/f).is_file(),f'file exists: {f}')
if errors: raise SystemExit('V45532_RELEASE_VALIDATION=FAIL: '+'; '.join(errors))
print('V45532_RELEASE_VALIDATION=PASS')
