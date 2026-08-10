from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.ocean_surface_v4500 import catalog, normalize_observation, readiness, state
CLIENT=TestClient(app); ROOT=Path(__file__).resolve().parents[2]

def test_overview_and_v4_architecture():
 p=CLIENT.get('/public/ocean-intelligence').json(); assert p['ok'] and p['version']=='4.14.0' and p['route']=='earth' and p['source_count']>=3 and p['variable_count']>=9 and len(p['contract_sha256'])==64; assert any('Missing ocean data remains missing' in x for x in p['truth_boundaries']); nav=CLIENT.get('/public/v4/navigation').json(); assert nav['route_count']==35 and nav['primary_area_count']==6

def test_catalog_sources_and_variables():
 p=catalog(); assert {x['id'] for x in p['sources']}=={'noaa-coastwatch-erddap','ioos-catalog','copernicus-marine'}; assert len(p['variables'])>=9; assert 'not global' in next(x for x in p['sources'] if x['id']=='ioos-catalog')['coverage']; assert 'free Copernicus Marine account' in next(x for x in p['sources'] if x['id']=='copernicus-marine')['authentication']

def test_state_does_not_fabricate_value_or_coverage():
 p=state('sea-surface-temperature','noaa-coastwatch-erddap',41.9,-87.6,'2026-08-09'); assert p['condition']['value'] is None and not p['condition']['record_loaded'] and not p['condition']['coverage_verified'] and not p['condition']['current_condition_claimed']; assert p['query_plan']['dataset_id']=='noaacwLEOACSPOSSTL3SnrtCDaily'; assert not p['truth']['value_fabricated'] and not p['truth']['missing_replaced'] and len(p['state_sha256'])==64

def test_bad_pair_and_coordinates_rejected():
 assert CLIENT.get('/public/ocean-intelligence/state',params={'variable':'sea-ice-concentration','source':'ioos-catalog'}).status_code==400; assert CLIENT.get('/public/ocean-intelligence/state',params={'latitude':95}).status_code==400

def test_source_attributed_record_normalization():
 p=normalize_observation({'variable_id':'sea-surface-temperature','source_id':'noaa-coastwatch-erddap','source_url':'https://coastwatch.noaa.gov/erddap/','evidence_type':'satellite-derived','value':24.2,'unit':'degC','latitude':18.5,'longitude':-66.1,'observed_at':'2026-08-08T12:00:00Z','source_record_id':'fixture'}); r=p['ocean_record']; assert r['source_domain_recognized'] and not r['network_response_independently_verified'] and r['evidence_state']=='source-attributed-not-network-verified' and not r['current_condition_claimed'] and len(p['record_sha256'])==64

def test_unregistered_source_host_and_evidence_type_rejected():
 base={'variable_id':'sea-surface-temperature','source_id':'noaa-coastwatch-erddap','source_url':'https://example.com/fake','evidence_type':'satellite-derived','value':20,'latitude':0,'longitude':0,'observed_at':'2026-08-09T00:00:00Z'}; assert CLIENT.post('/public/ocean-intelligence/observation/normalize',json=base).status_code==400; base['source_url']='https://coastwatch.noaa.gov/erddap/'; base['evidence_type']='forecast'; assert CLIENT.post('/public/ocean-intelligence/observation/normalize',json=base).status_code==400

def test_export_and_readiness():
 p=CLIENT.get('/public/ocean-intelligence/export-manifest',params={'variable':'surface-currents','source':'copernicus-marine','latitude':0,'longitude':-140,'date':'2026-08-09'}).json(); assert p['schema']=='sc-site-intelligence-ocean-surface/1.0' and not p['review']['surface_value_fabricated'] and not p['review']['evidence_classes_collapsed'] and not p['review']['missing_imputed'] and len(p['manifest_sha256'])==64; r=readiness(); assert r['ok'] and r['summary']['public_route_count_delta']==0

def test_assets_ship_in_app_service_worker_and_wordpress():
 html=(ROOT/'backend/public_app/index.html').read_text(); sw=(ROOT/'backend/public_app/service-worker.js').read_text(); js=(ROOT/'backend/public_app/assets/ocean-surface-v4500.js').read_text(); css=(ROOT/'backend/public_app/assets/ocean-surface-v4500.css').read_text(); assert 'ocean-surface-v4500.js' in html; assert 'ocean-surface-v4500.js' in sw and 'ocean-surface-v4500.css' in sw; assert 'SCSIOceanSurfaceV4500' in js and 'NO MEASUREMENT RENDERED' in js and '.ocean4500-stage' in css; assert js==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/ocean-surface-v4500.js').read_text(); assert css==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/ocean-surface-v4500.css').read_text()
