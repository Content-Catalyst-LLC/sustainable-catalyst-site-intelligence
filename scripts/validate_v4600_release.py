#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); ocean=(ROOT/'backend/public_app/assets/ocean-surface-v4500.js').read_text()
assert 'water-column-v4600.js' in ocean
assert 'water-column-v4600.js' in sw and 'water-column-v4600.css' in sw
assert (ROOT/'backend/public_app/assets/water-column-v4600.js').read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.js').read_text()
assert (ROOT/'backend/public_app/assets/water-column-v4600.css').read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.css').read_text()
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4600_release_contract.py')],check=True)
print('PASS: v4.13.0 static release validation')
