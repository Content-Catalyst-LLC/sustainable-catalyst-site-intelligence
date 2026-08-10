from fastapi.testclient import TestClient
from app.main import app
from app.cryosphere_v41600 import catalog,export_manifest,normalize_feature,normalize_measurement,anomaly_preview,readiness,state
CLIENT=TestClient(app)
def test_catalog_sources_and_truth():
 c=catalog(); assert {x['id'] for x in c['sources']}=={'noaa-nsidc-sea-ice-index','nasa-nsidc-daac','glims','modis-snow-sea-ice'}; assert c['truth_boundaries']['near_real_time_equals_final'] is False
def test_state_truth():
 s=state('noaa-nsidc-sea-ice-index','sea-ice-extent',80,-30,'2026-08-09'); assert s['source_supports_indicator_type']; assert not s['truth']['near_real_time_treated_as_final']; assert not s['truth']['missing_data_treated_as_no_ice_or_snow']; assert not s['truth']['local_safety_determination']
def test_measurement_normalization():
 m=normalize_measurement({'source_id':'noaa-nsidc-sea-ice-index','source_url':'https://noaadata.apps.nsidc.org/NOAA/G02135/','indicator_type':'sea-ice-extent','evidence_class':'satellite-derived','value':7.1,'unit':'million km2','temporal_status':'near-real-time'})['measurement']; assert m['temporal_status']=='near-real-time'; assert not m['near_real_time_treated_as_final']; assert not m['hazard_declaration']
def test_bad_host():
 r=CLIENT.post('/public/cryosphere/measurement/normalize',json={'source_id':'glims','source_url':'https://example.com/x','indicator_type':'glacier-area','evidence_class':'inventory-geometry','value':4,'unit':'km2'}); assert r.status_code==400
def test_glacier_inventory_not_mass_balance():
 f=normalize_feature({'source_id':'glims','source_url':'https://nsidc.org/data/glims','indicator_type':'glacier-outline','evidence_class':'inventory-geometry','bbox':[-150,60,-149,61],'source_date':'2024-07-01'})['feature']; assert not f['inventory_geometry_treated_as_current_position']; assert not f['glacier_mass_balance_inferred']; assert not f['hazard_declaration']
def test_model_not_observation():
 m=normalize_measurement({'source_id':'nasa-nsidc-daac','source_url':'https://cmr.earthdata.nasa.gov/search/collections.json','indicator_type':'frozen-ground','evidence_class':'model-analysis','value':1,'unit':'class'})['measurement']; assert not m['model_analysis_treated_as_observation']; assert not m['local_safety_determination']
def test_anomaly_preview_not_hazard():
 p=anomaly_preview({'current_value':5.2,'baseline_value':6.1,'unit':'million km2','reference_period':'1981-2010'})['preview']; assert p['delta']<0; assert not p['anomaly_is_hazard_declaration']; assert not p['causal_attribution_inferred']; assert not p['future_condition_predicted']
def test_manifest_readiness_architecture():
 p=export_manifest(); assert p['schema']=='sc-site-intelligence-cryosphere/1.0'; assert not p['review']['local_safety_determination']; r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
