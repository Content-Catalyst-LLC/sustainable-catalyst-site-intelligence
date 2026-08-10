#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8878'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(60):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/terrestrial-ecosystems',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('terrestrial server did not start')
 for path in ['/public/terrestrial-ecosystems','/public/terrestrial-ecosystems/catalog','/public/terrestrial-ecosystems/state?source=nasa-firms&indicator_type=active-fire-detection&latitude=41.88&longitude=-87.63','/public/terrestrial-ecosystems/readiness','/app/assets/terrestrial-ecosystems-v41900.js','/app/assets/terrestrial-ecosystems-v41900.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/terrestrial-ecosystems/state?source=nasa-firms&indicator_type=active-fire-detection',timeout=5).json(); assert s['truth']['active_fire_treated_as_burned_area'] is False and s['truth']['platform_wildfire_warning_issued'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/terrestrial-ecosystems-v41900.js',timeout=5).text; assert 'SCSITerrestrialEcosystemsV41900' in js and 'NOT A WILDFIRE INCIDENT, SAFETY OR ECOSYSTEM-HEALTH DETERMINATION' in js
 print('PASS: v4.19.0 terrestrial ecosystems direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except: p.kill()
