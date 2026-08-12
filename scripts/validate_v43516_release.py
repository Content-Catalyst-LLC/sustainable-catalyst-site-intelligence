#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43516_release_contract.py')],check=True)
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.35.20' in wp and 'site-intelligence-v4.35.20' in wp
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text()
assert 'data-scsi-release="4.35.20"' in index and 'const APP_VERSION="4.35.20"' in app
for marker in ('CREDENTIAL & CONFIGURATION CONTROL PLANE · v4.35.20','credentialConfigurationStatus','credentialProfileList'):
    assert marker in index,marker
for marker in ('renderCredentialConfiguration','/public/credential-configuration'):
    assert marker in app,marker
for f in ('backend/app/credential_configuration_v43516.py','backend/app/authoritative_api_audit_v43516.py','backend/app/authoritative_api_production_audit_v43516.py','backend/app/release_health_v43516.py','backend/tests/test_credentials_api_key_configuration_completion_v43516.py'):
    assert (ROOT/f).is_file(),f
print('PASS: v4.35.20 static release validation')
