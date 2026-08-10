#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1]; mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text()); assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[])), 'runtime state must not be frozen under backend/backend/'
assert not (ROOT/'backend/backend').exists(), 'nested backend runtime state must be absent before release validation'
sw=(ROOT/'backend/public_app/service-worker.js').read_text(); prev=(ROOT/'backend/public_app/assets/terrestrial-ecosystems-v41900.js').read_text()
assert 'geosphere-v42000.js' in prev; assert 'geosphere-v42000.js' in sw and 'geosphere-v42000.css' in sw
for asset in ('geosphere-v42000.js','geosphere-v42000.css','terrestrial-ecosystems-v41900.js','terrestrial-ecosystems-v41900.css'):
 assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(),asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v42000_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.20.0 static release validation')
