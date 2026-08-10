#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); uw=(ROOT/'backend/public_app/assets/underwater-observation-v4800.js').read_text()
assert 'marine-biodiversity-v4900.js' in uw
assert 'marine-biodiversity-v4900.js' in sw and 'marine-biodiversity-v4900.css' in sw
for asset in ('marine-biodiversity-v4900.js','marine-biodiversity-v4900.css','underwater-observation-v4800.js','underwater-observation-v4800.css'):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4900_release_contract.py')],check=True)
print('PASS: v4.16.0 static release validation')
