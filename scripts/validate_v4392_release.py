#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/validate_v4392_release_contract.py')],check=True)
p=ROOT/'MANIFEST.json'
if not p.is_file(): raise SystemExit('FAIL: MANIFEST.json missing')
data=json.loads(p.read_text(encoding='utf-8'))
if data.get('release')!='4.39.2': raise SystemExit('FAIL: manifest release is not 4.39.2')
if data.get('file_count')!=len(data.get('files',[])): raise SystemExit('FAIL: manifest file count mismatch')
print('PASS: v4.39.2 static release validation')
