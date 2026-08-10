#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8879'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(60):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/geosphere',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('geosphere server did not start')
 for path in ['/public/geosphere','/public/geosphere/catalog','/public/geosphere/state?source=usgs-earthquake-catalog&indicator_type=earthquake-event&latitude=41.88&longitude=-87.63','/public/geosphere/readiness','/app/assets/geosphere-v42000.js','/app/assets/geosphere-v42000.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/geosphere/state?source=usgs-earthquake-catalog&indicator_type=earthquake-event',timeout=5).json(); assert s['truth']['catalog_event_treated_as_emergency_warning'] is False and s['truth']['zero_records_treated_as_no_hazard'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/geosphere-v42000.js',timeout=5).text; assert 'SCSIGeosphereV42000' in js and 'NOT AN EMERGENCY, DAMAGE OR HAZARD DETERMINATION' in js
 print('PASS: v4.20.0 geosphere direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except: p.kill()
