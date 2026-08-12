#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text(); main=(ROOT/'backend/app/main.py').read_text()
assert 'data-scsi-release="4.35.16"' in index
assert 'CREDENTIAL & CONFIGURATION CONTROL PLANE · v4.35.16' in index
for marker in ('credentialProfilesMetric','credentialConfiguredMetric','credentialMissingMetric','credentialMappedMetric','credentialProfileList'):
    assert marker in index,marker
for marker in ('renderCredentialConfiguration','/public/credential-configuration','Missing credentials do not block deployment'):
    assert marker in app,marker
for endpoint in ('/public/credential-configuration','/public/credential-configuration/readiness','/public/credential-configuration/workspaces'):
    assert endpoint in main,endpoint
assert 'masked_value' not in app and 'secret_fingerprint' not in app
print('PASS: v4.35.16 credential/configuration browser/static gate')
