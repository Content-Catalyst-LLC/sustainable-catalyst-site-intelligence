#!/usr/bin/env python3
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; backend=ROOT/'backend'; py=os.environ.get('PYTHON',sys.executable); port='8882'; env={**os.environ,'PYTHONPATH':str(backend)}
p=subprocess.Popen([py,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',port],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 import httpx
 for _ in range(80):
  try:
   if httpx.get(f'http://127.0.0.1:{port}/public/biodiversity',timeout=1).status_code==200: break
  except Exception: time.sleep(.1)
 else: raise SystemExit('biodiversity server did not start')
 for path in ['/public/biodiversity','/public/biodiversity/catalog','/public/biodiversity/state?source=gbif-occurrence&indicator_type=species-occurrence&scientific_name=Danaus%20plexippus','/public/biodiversity/readiness','/app/assets/biodiversity-v42300.js','/app/assets/biodiversity-v42300.css']:
  r=httpx.get(f'http://127.0.0.1:{port}'+path,timeout=5); assert r.status_code==200,(path,r.status_code)
 s=httpx.get(f'http://127.0.0.1:{port}/public/biodiversity/state?source=usfws-ecos&indicator_type=esa-listing-status',timeout=5).json(); assert s['truth']['esa_status_treated_as_global_status'] is False and s['truth']['critical_habitat_overlap_treated_as_project_effect'] is False
 js=httpx.get(f'http://127.0.0.1:{port}/app/assets/biodiversity-v42300.js',timeout=5).text; assert 'SCSIBiodiversityV42300' in js and 'NOT A POPULATION CENSUS, ABSENCE FINDING OR LEGAL DETERMINATION' in js
 print('PASS: v4.23.0 biodiversity direct and iframe-compatible HTTP/browser asset gate')
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except: p.kill()
