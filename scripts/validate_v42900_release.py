#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1];mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text());assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[]))
assert not (ROOT/'backend/backend').exists()
sw=(ROOT/'backend/public_app/service-worker.js').read_text();prev=(ROOT/'backend/public_app/assets/energy-systems-v42800.js').read_text()
assert 'digital-connectivity-v42900.js' in prev and 'digital-connectivity-v42900.js' in sw and 'digital-connectivity-v42900.css' in sw
for a in ('digital-connectivity-v42900.js','digital-connectivity-v42900.css','energy-systems-v42800.js','energy-systems-v42800.css'):
 assert (ROOT/'backend/public_app/assets'/a).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/a).read_text(),a
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v42900_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.29.0 static release validation')
