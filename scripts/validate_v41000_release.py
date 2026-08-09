#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); bio=(ROOT/'backend/public_app/assets/marine-biodiversity-v4900.js').read_text()
assert 'ocean-missions-v41000.js' in bio
assert 'ocean-missions-v41000.js' in sw and 'ocean-missions-v41000.css' in sw
for asset in ('ocean-missions-v41000.js','ocean-missions-v41000.css','marine-biodiversity-v4900.js','marine-biodiversity-v4900.css'):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v41000_release_contract.py')],check=True)
print('PASS: v4.11.0 static release validation')
