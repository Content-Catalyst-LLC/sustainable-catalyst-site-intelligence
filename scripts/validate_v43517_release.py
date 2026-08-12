#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / 'scripts/validate_v43517_release_contract.py')], check=True)
wp = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.35.22' in wp and 'site-intelligence-v4.35.22' in wp
index = (ROOT / 'backend/public_app/index.html').read_text()
app = (ROOT / 'backend/public_app/assets/app.js').read_text()
assert 'data-scsi-release="4.35.22"' in index
assert 'const APP_VERSION="4.35.22"' in app
for marker in ('EXTERNAL RESILIENCE · v4.35.22', 'externalResilienceStatus', 'resilienceCircuitMetric'):
    assert marker in index, marker
for marker in ('renderExternalResilience', '/public/external-resilience'):
    assert marker in app, marker
for file in (
    'backend/app/external_resilience_v43517.py',
    'backend/app/release_health_v43517.py',
    'backend/tests/test_external_resilience_v43517.py',
):
    assert (ROOT / file).is_file(), file
print('PASS: v4.35.22 static release validation')
