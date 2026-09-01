#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4370_release_contract.py')],check=True)
manifest=ROOT/'MANIFEST.json'
if not manifest.is_file(): raise SystemExit('FAIL: MANIFEST.json missing')
data=json.loads(manifest.read_text())
if data.get('release')!='4.39.0': raise SystemExit('FAIL: manifest release is not 4.39.0')
if not (ROOT/'backend/tests/test_live_underwater_media_v4370.py').is_file(): raise SystemExit('FAIL: v4.39.0 tests missing')
if not (ROOT/'scripts/browser_underwater_media_v4370.py').is_file(): raise SystemExit('FAIL: v4.39.0 browser gate missing')
print('PASS: v4.39.0 static release validation')
