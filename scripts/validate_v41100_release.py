#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); missions=(ROOT/'backend/public_app/assets/ocean-missions-v41000.js').read_text()
assert 'ocean-events-v41100.js' in missions
assert 'ocean-events-v41100.js' in sw and 'ocean-events-v41100.css' in sw
for asset in ('ocean-events-v41100.js','ocean-events-v41100.css','ocean-missions-v41000.js','ocean-missions-v41000.css'):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v41100_release_contract.py')],check=True)
print('PASS: v4.15.0 static release validation')
