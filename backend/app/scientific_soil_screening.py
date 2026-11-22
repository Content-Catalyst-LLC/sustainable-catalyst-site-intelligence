"""Verified Irish soil catalog snapshots, using Library as artifact authority.

No parcels, field observations or removal surfaces are inferred from the national
association catalog. Source terms and the published map CRS/scale are retained.
"""
import hashlib,hmac,json,os
from urllib.request import Request,build_opener,HTTPRedirectHandler,ProxyHandler
from urllib.error import URLError
from fastapi import APIRouter,Depends,Header,HTTPException
from .config import get_settings
from . import soils_land_degradation_v42100 as soils
SOURCE_ID='teagasc-irish-soil-associations'
SOURCE={'title':'Teagasc Irish National Soils Map V1b','organization':'Teagasc and Cranfield University; EPA STRIVE',
 'url':'https://gis.teagasc.ie/soils/downloads.php','api_url':'https://gis.teagasc.ie/soils/services/get_all_associations.php',
 'recognized_hosts':['gis.teagasc.ie'],'indicator_types':['soil-taxonomic-class'],'evidence_classes':['official-soil-survey-mapunit'],
 'coverage':'Ireland; national 1:250,000 soil association map, V1b (2014-09-30), EPSG:29902.',
 'limitations':'Generalized survey/model map for reconnaissance. Personal and research use only; other applications require written agreement. No parcel truth or carbon-removal conclusion.'}
soils.SOURCES[SOURCE_ID]=SOURCE
router=APIRouter(prefix='/v1/scientific-screening',tags=['scientific-soil-screening'])
def require_scientific_access(x_sc_intelligence_token:str|None=Header(default=None)):
 expected=get_settings().api_token
 if not expected or expected=='dev-token-change-me':raise HTTPException(503,'Scientific screening credential is not configured.')
 if not x_sc_intelligence_token or not hmac.compare_digest(x_sc_intelligence_token.encode(),expected.encode()):raise HTTPException(401,'Scientific screening authorization required.')
def snapshot():
 library=os.getenv('SC_SI_SCIENTIFIC_LIBRARY_URL','').rstrip('/');key=os.getenv('SC_SI_SCIENTIFIC_LIBRARY_KEY','')
 readme_sha=os.getenv('SC_SI_TEAGASC_README_SHA256','');catalog_sha=os.getenv('SC_SI_TEAGASC_CATALOG_SHA256','')
 import re
 if not library or not key or not all(re.fullmatch('[a-f0-9]{64}',s) for s in [readme_sha,catalog_sha]):raise HTTPException(503,'Verified Teagasc source snapshots are unavailable.')
 class NoRedirect(HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):return None
 def fetch(sha):
  try:
   with build_opener(ProxyHandler({}),NoRedirect()).open(Request(library+'/v1/admin/artifacts/artifact:sha256:'+sha+'/content',headers={'Authorization':'Bearer '+key}),timeout=20) as r:raw=r.read(1_000_001)
  except URLError as exc:raise HTTPException(502,'Library source retrieval failed.') from exc
  if len(raw)>1_000_000 or hashlib.sha256(raw).hexdigest()!=sha:raise HTTPException(409,'Scientific source snapshot integrity mismatch.')
  return raw
 readme=fetch(readme_sha);raw=fetch(catalog_sha)
 if not readme.startswith(b'%PDF'):raise HTTPException(422,'Original publisher usage guide is not a PDF.')
 try:
  associations=json.loads(raw)
  if not isinstance(associations,list) or not associations or len(associations)>5000:raise ValueError()
  rows=[{'code':str(x['Association_Unit']),'name':str(x['Association_Name']),'rgb':[int(x[k]) for k in ['Red_Value','Green_Value','Blue_Value']]} for x in associations]
  if any(not all(0<=v<=255 for v in row['rgb']) for row in rows):raise ValueError()
 except (ValueError,KeyError,TypeError) as exc:raise HTTPException(422,'Invalid official association catalog.') from exc
 return {'schema':'sc-site-intelligence-scientific-screening-snapshot/1.0','source':{'id':SOURCE_ID,**SOURCE},'associations':rows,
 'source_artifacts':['artifact:sha256:'+readme_sha,'artifact:sha256:'+catalog_sha],
 'crs':'EPSG:29902','scale_denominator':250000,'data_version':'1b (2014-09-30)',
 'rights':{'reference':'https://gis.teagasc.ie/soils/downloads/IrishSoilMap1b_Readme.pdf','scope':'personal-and-research-only','other_use_requires_written_agreement':True},
 'status':'SCREENING_ONLY','catalog_loaded':True,'map_geometry_loaded':False,'site_boundaries':None,'field_observations':None,
 'net_removal_surface_available':False,'net_removal_status':'NOT_QUANTIFIED','human_source_review':'pending',
 'blockers':['Permissioned farm boundaries, field measurements, verified drainage layers and model uncertainty are unavailable.']}
@router.get('/irish-soils',dependencies=[Depends(require_scientific_access)])
def irish_soils():return snapshot()
