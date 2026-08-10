#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1];mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text());assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[]))
assert not (ROOT/'backend/backend').exists()
sw=(ROOT/'backend/public_app/service-worker.js').read_text();prev=(ROOT/'backend/public_app/assets/digital-connectivity-v42900.js').read_text()
assert 'industrial-manufacturing-v43000.js' in prev and 'industrial-manufacturing-v43000.js' in sw and 'industrial-manufacturing-v43000.css' in sw
for a in ('industrial-manufacturing-v43000.js','industrial-manufacturing-v43000.css','digital-connectivity-v42900.js','digital-connectivity-v42900.css'):
 assert (ROOT/'backend/public_app/assets'/a).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/a).read_text(),a
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43000_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.30.0 static release validation')
