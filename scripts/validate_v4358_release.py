#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4358_release_contract.py')],check=True)
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
assert 'Version: 4.35.10' in wp and 'site-intelligence-v4.35.10' in wp
index=(ROOT/'backend/public_app/index.html').read_text(); app=(ROOT/'backend/public_app/assets/app.js').read_text()
assert 'data-scsi-release="4.35.10"' in index and 'const APP_VERSION="4.35.10"' in app
for f in ('backend/app/workspace_evidence_unification_v4358.py','backend/app/record_provenance_v4358.py','backend/tests/test_workspace_evidence_unification_truth_layer_v4358.py'):
    assert (ROOT/f).is_file(),f
print('PASS: v4.35.10 static release validation')
