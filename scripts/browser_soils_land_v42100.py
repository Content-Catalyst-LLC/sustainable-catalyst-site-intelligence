#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8880'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(80):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/soils-land',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('soils/land server did not start')
 for path in ['/public/soils-land','/public/soils-land/catalog','/public/soils-land/state?source=isric-soilgrids&indicator_type=soil-organic-carbon&latitude=41.88&longitude=-87.63','/public/soils-land/readiness','/app/assets/soils-land-v42100.js','/app/assets/soils-land-v42100.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/soils-land/state?source=isric-soilgrids&indicator_type=soil-organic-carbon',timeout=5).json(); assert s['truth']['soilgrids_treated_as_ground_sample'] is False and s['truth']['zero_records_treated_as_healthy_soil'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/soils-land-v42100.js',timeout=5).text; assert 'SCSISoilsLandV42100' in js and 'NOT A SITE INVESTIGATION, LAND-DEGRADATION DECLARATION OR CARBON CLAIM' in js
 print('PASS: v4.21.0 soils/land direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except: p.kill()
