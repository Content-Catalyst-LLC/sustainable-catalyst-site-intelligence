#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1];mp=ROOT/'MANIFEST.json'
if mp.exists():
 m=json.loads(mp.read_text());assert not any(r['path'].startswith('backend/backend/') for r in m.get('files',[]))
assert not (ROOT/'backend/backend').exists()
sw=(ROOT/'backend/public_app/service-worker.js').read_text();astro=(ROOT/'backend/public_app/assets/astronomical-observation-v4300.js').read_text()
assert 'exoplanet-habitability-v43500.js' in sw and 'exoplanet-habitability-v43500.css' in sw
assert 'astroExoplanets' in astro and 'SCSIExoplanetHabitabilityV43500' in astro
assert 'exoplanet-habitability-v43500.js?v=4.35.1' in astro and 'exoplanet-habitability-v43500.css?v=4.35.1' in astro
for a in ('exoplanet-habitability-v43500.js','exoplanet-habitability-v43500.css','astronomical-observation-v4300.js','astronomical-observation-v4300.css'):
 assert (ROOT/'backend/public_app/assets'/a).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/a).read_text(),a
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v43500_release_contract.py')],check=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.35.1 static release validation')
