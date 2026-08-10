from fastapi.testclient import TestClient
from app.main import app
from app.hydrology_v41800 import catalog,export_manifest,normalize_forecast,normalize_measurement,threshold_preview,readiness,state
CLIENT=TestClient(app)
def test_catalog_sources_and_truth():
 c=catalog(); assert {x['id'] for x in c['sources']}=={'usgs-water-data','nasa-gpm-imerg','copernicus-glofas','drought-gov'}; assert c['truth_boundaries']['threshold_equals_official_flood_warning'] is False
def test_state_truth():
 s=state('usgs-water-data','streamflow',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type']; assert not s['truth']['model_discharge_treated_as_gauge_observation']; assert not s['truth']['official_flood_warning_issued_by_platform']; assert not s['truth']['zero_records_treated_as_no_flood_or_drought']
def test_usgs_gauge_normalization():
 m=normalize_measurement({'source_id':'usgs-water-data','source_url':'https://api.waterdata.usgs.gov/','indicator_type':'streamflow','evidence_class':'in-situ-observation','value':1200,'unit':'ft3/s'})['measurement']; assert not m['model_discharge_treated_as_gauge_observation']; assert not m['official_flood_warning_issued_by_platform']
def test_bad_host():
 r=CLIENT.post('/public/hydrology/measurement/normalize',json={'source_id':'usgs-water-data','source_url':'https://example.com/x','indicator_type':'streamflow','evidence_class':'in-situ-observation','value':4}); assert r.status_code==400
def test_imerg_satellite_not_gauge():
 m=normalize_measurement({'source_id':'nasa-gpm-imerg','source_url':'https://gpm.nasa.gov/data/imerg','indicator_type':'precipitation-rate','evidence_class':'satellite-estimate','value':12.4,'unit':'mm/hr'})['measurement']; assert not m['satellite_precipitation_treated_as_gauge_observation']
def test_glofas_model_not_gauge():
 m=normalize_measurement({'source_id':'copernicus-glofas','source_url':'https://global-flood.emergency.copernicus.eu/','indicator_type':'river-discharge','evidence_class':'model-analysis','value':450,'unit':'m3/s'})['measurement']; assert not m['model_discharge_treated_as_gauge_observation']
def test_forecast_and_threshold_truth():
 f=normalize_forecast({'source_id':'copernicus-glofas','source_url':'https://global-flood.emergency.copernicus.eu/','indicator_type':'river-discharge','evidence_class':'forecast','value':800,'unit':'m3/s','lead_time_hours':72})['forecast']; assert not f['forecast_treated_as_observation']; assert not f['platform_warning_created']; p=threshold_preview({'value':800,'threshold':700,'operator':'>=','unit':'m3/s'})['preview']; assert p['comparison']; assert not p['official_flood_warning']; assert not p['drought_declaration']; assert not p['emergency_warning']
def test_manifest_readiness_architecture():
 p=export_manifest(); assert p['schema']=='sc-site-intelligence-hydrology/1.0'; assert not p['review']['official_flood_warning']; r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
