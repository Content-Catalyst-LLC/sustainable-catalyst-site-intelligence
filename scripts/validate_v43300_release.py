#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1];mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text());assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[]))
assert not (ROOT/'backend/backend').exists()
sw=(ROOT/'backend/public_app/service-worker.js').read_text();prev=(ROOT/'backend/public_app/assets/water-sanitation-v43200.js').read_text()
assert 'solid-waste-circular-v43300.js' in prev and 'solid-waste-circular-v43300.js' in sw and 'solid-waste-circular-v43300.css' in sw
for a in ('solid-waste-circular-v43300.js','solid-waste-circular-v43300.css','water-sanitation-v43200.js','water-sanitation-v43200.css'):
 assert (ROOT/'backend/public_app/assets'/a).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/a).read_text(),a
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43300_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.35.0 static release validation')
