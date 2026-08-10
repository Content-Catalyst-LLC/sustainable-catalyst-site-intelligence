#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); sea=(ROOT/'backend/public_app/assets/seafloor-bathymetry-v4700.js').read_text()
assert 'underwater-observation-v4800.js' in sea
assert 'underwater-observation-v4800.js' in sw and 'underwater-observation-v4800.css' in sw
for asset in ('underwater-observation-v4800.js','underwater-observation-v4800.css','seafloor-bathymetry-v4700.js','seafloor-bathymetry-v4700.css'):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4800_release_contract.py')],check=True)
print('PASS: v4.15.0 static release validation')
