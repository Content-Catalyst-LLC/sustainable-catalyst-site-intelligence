#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8881'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(80):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/climate',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('climate server did not start')
 for path in ['/public/climate','/public/climate/catalog','/public/climate/state?source=nasa-gistemp-v4&indicator_type=global-temperature-anomaly','/public/climate/readiness','/app/assets/climate-v42200.js','/app/assets/climate-v42200.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/climate/state?source=copernicus-era5&indicator_type=climate-anomaly',timeout=5).json(); assert s['truth']['era5_treated_as_direct_observation'] is False and s['truth']['zero_records_treated_as_no_climate_risk'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/climate-v42200.js',timeout=5).text; assert 'SCSIClimateV42200' in js and 'NOT A WEATHER FORECAST, ATTRIBUTION FINDING OR RECORD CERTIFICATION' in js
 print('PASS: v4.22.0 climate direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except: p.kill()
