#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v4390_release_contract.py")], check=True)
manifest = ROOT / "MANIFEST.json"
if not manifest.is_file():
    raise SystemExit("FAIL: MANIFEST.json missing")
data = json.loads(manifest.read_text(encoding="utf-8"))
if data.get("release") != "4.39.1":
    raise SystemExit("FAIL: manifest release is not 4.39.1")
if data.get("file_count") != len(data.get("files", [])):
    raise SystemExit("FAIL: manifest file count mismatch")
print("PASS: v4.39.1 static release validation")
