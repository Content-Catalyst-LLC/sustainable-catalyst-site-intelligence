#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, os, json
ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'MANIFEST.json'
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    assert not any(row['path'].startswith('backend/backend/') for row in manifest.get('files', [])), 'runtime state must not be frozen under backend/backend/'
assert not (ROOT / 'backend/backend').exists(), 'nested backend runtime state must be absent before release validation'
sw = (ROOT / 'backend/public_app/service-worker.js').read_text()
pollution = (ROOT / 'backend/public_app/assets/marine-pollution-v41300.js').read_text()
assert 'coastal-change-v41400.js' in pollution
assert 'coastal-change-v41400.js' in sw and 'coastal-change-v41400.css' in sw
for asset in (
    'coastal-change-v41400.js','coastal-change-v41400.css',
    'marine-pollution-v41300.js','marine-pollution-v41300.css',
):
    assert (ROOT/'backend/public_app/assets'/asset).read_text() == (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/asset).read_text(), asset
subprocess.run([sys.executable, str(ROOT/'scripts/validate_v41400_release_contract.py')], check=True, cwd=ROOT, env={**os.environ, 'PYTHONPATH':str(ROOT/'backend')})
print('PASS: v4.15.0 static release validation')
