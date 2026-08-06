#!/usr/bin/env python3
"""Run every pytest file in its own process and reject hangs as failures."""
from __future__ import annotations
import os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BACKEND=ROOT/'backend';PYTHON=os.environ.get('PYTHON') or sys.executable;TIMEOUT=int(os.environ.get('SC_SI_TEST_FILE_TIMEOUT','60'))
env={**os.environ,'PYTHONPATH':str(BACKEND),'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}
collect=subprocess.run([PYTHON,'-m','pytest','--collect-only','-q'],cwd=BACKEND,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
match=re.search(r'(\d+) tests collected',collect.stdout);collected=int(match.group(1)) if match else 0
files=sorted((BACKEND/'tests').glob('test_*.py'))
for index,path in enumerate(files,1):
    rel=path.relative_to(BACKEND)
    print(f'[{index}/{len(files)}] {rel}',flush=True)
    try:
        result=subprocess.run([PYTHON,'-m','pytest','-q','--disable-warnings',str(rel)],cwd=BACKEND,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        output=exc.stdout or ''
        if isinstance(output,bytes):output=output.decode(errors='replace')
        if output:print(output.rstrip())
        raise SystemExit(f'ERROR: {rel} did not exit within {TIMEOUT} seconds.')
    if result.returncode:
        print(result.stdout.rstrip())
        raise SystemExit(f'ERROR: pytest failed for {rel}.')
print(f'PASS: all {collected} collected tests passed across {len(files)} independently exiting test processes.')
