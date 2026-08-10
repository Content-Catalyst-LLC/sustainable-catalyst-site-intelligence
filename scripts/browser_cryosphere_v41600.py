#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8876'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(60):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/cryosphere',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('cryosphere server did not start')
 for path in ['/public/cryosphere','/public/cryosphere/catalog','/public/cryosphere/state?source=noaa-nsidc-sea-ice-index&indicator_type=sea-ice-extent&latitude=80&longitude=-30','/public/cryosphere/readiness','/app/assets/cryosphere-v41600.js','/app/assets/cryosphere-v41600.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/cryosphere/state?source=noaa-nsidc-sea-ice-index&indicator_type=sea-ice-extent',timeout=5).json(); assert s['truth']['local_safety_determination'] is False
 print('PASS: v4.17.0 cryosphere direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate();
 try:p.wait(timeout=5)
 except: p.kill()
