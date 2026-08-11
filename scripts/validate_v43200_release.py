#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1];mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text());assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[]))
assert not (ROOT/'backend/backend').exists()
sw=(ROOT/'backend/public_app/service-worker.js').read_text();prev=(ROOT/'backend/public_app/assets/mining-critical-materials-v43100.js').read_text()
assert 'water-sanitation-v43200.js' in prev and 'water-sanitation-v43200.js' in sw and 'water-sanitation-v43200.css' in sw
for a in ('water-sanitation-v43200.js','water-sanitation-v43200.css','mining-critical-materials-v43100.js','mining-critical-materials-v43100.css'):
 assert (ROOT/'backend/public_app/assets'/a).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/a).read_text(),a
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43200_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.35.1 static release validation')
