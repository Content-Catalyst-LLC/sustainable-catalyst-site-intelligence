#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8877'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(60):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/hydrology',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('atmosphere server did not start')
 for path in ['/public/hydrology','/public/hydrology/catalog','/public/hydrology/state?source=usgs-water-data&indicator_type=streamflow&latitude=41.88&longitude=-87.63','/public/hydrology/readiness','/app/assets/hydrology-v41800.js','/app/assets/hydrology-v41800.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/hydrology/state?source=usgs-water-data&indicator_type=streamflow',timeout=5).json(); assert s['truth']['model_discharge_treated_as_gauge_observation'] is False and s['truth']['official_flood_warning_issued_by_platform'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/hydrology-v41800.js',timeout=5).text; assert 'SCSIHydrologyV41800' in js and 'NOT AN OFFICIAL FLOOD, DROUGHT OR SAFETY WARNING' in js
 print('PASS: v4.18.0 hydrology direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate();
 try:p.wait(timeout=5)
 except: p.kill()
