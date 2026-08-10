#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
manifest_path=ROOT/'MANIFEST.json'
if manifest_path.exists():
    import json
    manifest=json.loads(manifest_path.read_text())
    assert not any(row['path'].startswith('backend/backend/') for row in manifest.get('files', [])), 'runtime state must not be frozen under backend/backend/'
assert not (ROOT/'backend/backend').exists(), 'nested backend runtime state must be absent before release validation'
sw=(ROOT/'backend/public_app/service-worker.js').read_text()
events=(ROOT/'backend/public_app/assets/ocean-events-v41100.js').read_text()
assert 'marine-human-activity-v41200.js' in events
assert 'marine-human-activity-v41200.js' in sw and 'marine-human-activity-v41200.css' in sw
for asset in (
    'marine-human-activity-v41200.js','marine-human-activity-v41200.css',
    'ocean-events-v41100.js','ocean-events-v41100.css',
):
    assert (ROOT/'backend/public_app/assets'/asset).read_text()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v41200_release_contract.py')],check=True,cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.16.0 static release validation')
