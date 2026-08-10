#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8877'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(60):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/atmosphere',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('atmosphere server did not start')
 for path in ['/public/atmosphere','/public/atmosphere/catalog','/public/atmosphere/state?source=airnow&indicator_type=aqi&latitude=41.88&longitude=-87.63','/public/atmosphere/readiness','/app/assets/atmosphere-v41700.js','/app/assets/atmosphere-v41700.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/atmosphere/state?source=airnow&indicator_type=aqi',timeout=5).json(); assert s['truth']['preliminary_treated_as_regulatory'] is False and s['truth']['health_advisory_issued_by_platform'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/atmosphere-v41700.js',timeout=5).text; assert 'SCSIAtmosphereV41700' in js and 'NOT A HEALTH, REGULATORY OR EMERGENCY DETERMINATION' in js
 print('PASS: v4.17.0 atmosphere direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate();
 try:p.wait(timeout=5)
 except: p.kill()
