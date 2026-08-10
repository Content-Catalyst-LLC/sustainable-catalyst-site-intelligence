#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); water=(ROOT/'backend/public_app/assets/water-column-v4600.js').read_text()
assert 'seafloor-bathymetry-v4700.js' in water
assert 'seafloor-bathymetry-v4700.js' in sw and 'seafloor-bathymetry-v4700.css' in sw
for asset in ('seafloor-bathymetry-v4700.js','seafloor-bathymetry-v4700.css'):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text()
assert (ROOT/'backend/public_app/assets/water-column-v4600.js').read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.js').read_text()
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4700_release_contract.py')],check=True)
print('PASS: v4.17.0 static release validation')
