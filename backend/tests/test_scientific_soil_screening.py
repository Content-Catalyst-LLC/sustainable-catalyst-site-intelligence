import hashlib,json
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import scientific_soil_screening as screening

def test_pinned_sources_auth_and_no_parcel_inference(monkeypatch):
 readme=b'%PDF-synthetic-test-only';catalog=json.dumps([{'Association_Unit':'synthetic','Association_Name':'Synthetic class','Red_Value':'1','Green_Value':'2','Blue_Value':'3'}]).encode()
 hashes=[hashlib.sha256(x).hexdigest() for x in [readme,catalog]]
 monkeypatch.setenv('SC_SI_SCIENTIFIC_LIBRARY_URL','http://library.test');monkeypatch.setenv('SC_SI_SCIENTIFIC_LIBRARY_KEY','synthetic-library-key')
 monkeypatch.setenv('SC_SI_TEAGASC_README_SHA256',hashes[0]);monkeypatch.setenv('SC_SI_TEAGASC_CATALOG_SHA256',hashes[1])
 monkeypatch.setattr(screening,'get_settings',lambda:SimpleNamespace(api_token='synthetic-screening-key'))
 class Reply:
  def __init__(self,raw):self.raw=raw
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self,n):return self.raw[:n]
 class Opener:
  def open(self,request,timeout):
   assert request.get_header('Authorization')=='Bearer synthetic-library-key'
   return Reply(readme if hashes[0] in request.full_url else catalog)
 monkeypatch.setattr(screening,'build_opener',lambda *args:Opener())
 app=FastAPI();app.include_router(screening.router);client=TestClient(app)
 path='/v1/scientific-screening/irish-soils'
 assert client.get(path).status_code==401
 r=client.get(path,headers={'X-SC-Intelligence-Token':'synthetic-screening-key'})
 assert r.status_code==200,r.text
 assert r.json()['catalog_loaded'] is True and r.json()['map_geometry_loaded'] is False
 assert r.json()['crs']=='EPSG:29902' and r.json()['site_boundaries'] is None
 assert r.json()['net_removal_surface_available'] is False
 monkeypatch.setenv('SC_SI_TEAGASC_README_SHA256','0'*64)
 assert client.get(path,headers={'X-SC-Intelligence-Token':'synthetic-screening-key'}).status_code==409
