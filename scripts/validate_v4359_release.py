#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4359_release_contract.py')],check=True)
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.35.14' in wp and 'site-intelligence-v4.35.14' in wp
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text()
assert 'data-scsi-release="4.35.14"' in index and 'const APP_VERSION="4.35.14"' in app
for f in ('backend/app/authoritative_api_production_audit_v4359.py','backend/tests/test_authoritative_api_coverage_closure_production_audit_v4359.py'):
 assert (ROOT/f).is_file(),f
print('PASS: v4.35.14 static release validation')
