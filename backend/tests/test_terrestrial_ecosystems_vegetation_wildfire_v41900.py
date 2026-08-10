from fastapi.testclient import TestClient
from app.main import app
from app.terrestrial_ecosystems_v41900 import catalog,export_manifest,normalize_feature,normalize_measurement,threshold_preview,readiness,state
CLIENT=TestClient(app)
def test_catalog_sources_and_truth():
 c=catalog(); assert {x['id'] for x in c['sources']}=={'nasa-firms','nasa-modis-vegetation','copernicus-lcfm','copernicus-global-vegetation'}; assert c['truth_boundaries']['active_fire_detection_equals_wildfire_incident'] is False
def test_state_truth():
 s=state('nasa-firms','active-fire-detection',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type']; assert not s['truth']['active_fire_treated_as_burned_area']; assert not s['truth']['platform_wildfire_warning_issued']; assert not s['truth']['zero_records_treated_as_no_fire_or_no_change']
def test_firms_detection_not_incident_or_burned_area():
 m=normalize_measurement({'source_id':'nasa-firms','source_url':'https://firms.modaps.eosdis.nasa.gov/','indicator_type':'active-fire-detection','evidence_class':'near-real-time-fire-detection','value':1,'unit':'detection'})['measurement']; assert not m['active_fire_treated_as_wildfire_incident']; assert not m['active_fire_treated_as_burned_area']; assert not m['platform_wildfire_warning_issued']
def test_bad_host():
 r=CLIENT.post('/public/terrestrial-ecosystems/measurement/normalize',json={'source_id':'nasa-firms','source_url':'https://example.com/x','indicator_type':'active-fire-detection','evidence_class':'near-real-time-fire-detection','value':1}); assert r.status_code==400
def test_modis_ndvi_not_ecosystem_health():
 m=normalize_measurement({'source_id':'nasa-modis-vegetation','source_url':'https://cmr.earthdata.nasa.gov/search/','indicator_type':'ndvi','evidence_class':'satellite-vegetation-index','value':0.61,'unit':'index'})['measurement']; assert not m['vegetation_index_treated_as_ecosystem_health']; assert not m['platform_ecosystem_health_finding']
def test_land_cover_not_legal_land_use_or_ground_truth():
 f=normalize_feature({'source_id':'copernicus-lcfm','source_url':'https://land.copernicus.eu/en/products/global-dynamic-land-cover','indicator_type':'land-cover-class','evidence_class':'satellite-land-cover','feature_id':'cell-1','class_label':'tree cover'})['feature']; assert not f['land_cover_treated_as_legal_land_use']; assert not f['satellite_classification_treated_as_ground_truth']
def test_burned_area_and_threshold_truth():
 f=normalize_feature({'source_id':'nasa-firms','source_url':'https://firms.modaps.eosdis.nasa.gov/','indicator_type':'burned-area','evidence_class':'satellite-burned-area','area_km2':12.4})['feature']; assert not f['burned_area_treated_as_active_fire']; p=threshold_preview({'value':20,'threshold':10,'operator':'>=','unit':'detections'})['preview']; assert p['comparison']; assert not p['wildfire_warning']; assert not p['evacuation_order']; assert not p['ecosystem_health_finding']
def test_manifest_readiness_architecture():
 p=export_manifest(); assert p['schema']=='sc-site-intelligence-terrestrial-ecosystems/1.0'; assert not p['review']['wildfire_warning']; r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
