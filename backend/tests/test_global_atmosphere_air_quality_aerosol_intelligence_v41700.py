from fastapi.testclient import TestClient
from app.main import app
from app.atmosphere_v41700 import catalog,export_manifest,normalize_forecast,normalize_measurement,threshold_preview,readiness,state
CLIENT=TestClient(app)
def test_catalog_sources_and_truth():
 c=catalog(); assert {x['id'] for x in c['sources']}=={'airnow','epa-aqs','cams-global','nasa-earthdata-aerosol'}; assert c['truth_boundaries']['airnow_preliminary_equals_regulatory'] is False
def test_state_truth():
 s=state('airnow','aqi',41.88,-87.63,'2026-08-09'); assert s['source_supports_indicator_type']; assert not s['truth']['preliminary_treated_as_regulatory']; assert not s['truth']['health_advisory_issued_by_platform']; assert not s['truth']['zero_records_treated_as_clean_air']
def test_airnow_preliminary_normalization():
 m=normalize_measurement({'source_id':'airnow','source_url':'https://docs.airnowapi.org/','indicator_type':'pm2.5','evidence_class':'preliminary-observation','value':18.2,'unit':'ug/m3'})['measurement']; assert not m['preliminary_treated_as_regulatory']; assert not m['regulatory_exceedance_declared']; assert not m['health_advisory_issued_by_platform']
def test_bad_host():
 r=CLIENT.post('/public/atmosphere/measurement/normalize',json={'source_id':'epa-aqs','source_url':'https://example.com/x','indicator_type':'pm2.5','evidence_class':'regulatory-monitor','value':4,'unit':'ug/m3'}); assert r.status_code==400
def test_cams_model_not_observation():
 m=normalize_measurement({'source_id':'cams-global','source_url':'https://ads.atmosphere.copernicus.eu/','indicator_type':'ozone','evidence_class':'model-analysis','value':65,'unit':'ug/m3'})['measurement']; assert not m['model_analysis_treated_as_observation']; assert not m['regulatory_exceedance_declared']
def test_nasa_aod_not_pm25():
 m=normalize_measurement({'source_id':'nasa-earthdata-aerosol','source_url':'https://www.earthdata.nasa.gov/topics/atmosphere/air-quality','indicator_type':'aerosol-optical-depth','evidence_class':'satellite-derived','value':0.4,'unit':'1'})['measurement']; assert not m['aod_treated_as_surface_pm25']
def test_forecast_and_threshold_truth():
 f=normalize_forecast({'source_id':'airnow','source_url':'https://docs.airnowapi.org/webservices','indicator_type':'aqi','evidence_class':'forecast','value':110,'unit':'AQI'})['forecast']; assert not f['forecast_treated_as_observation']; assert not f['platform_advisory_created']; p=threshold_preview({'value':110,'threshold':100,'operator':'>=','unit':'AQI'})['preview']; assert p['comparison']; assert not p['regulatory_exceedance']; assert not p['health_advisory']; assert not p['emergency_warning']
def test_manifest_readiness_architecture():
 p=export_manifest(); assert p['schema']=='sc-site-intelligence-atmosphere/1.0'; assert not p['review']['health_advisory']; r=readiness(); assert r['ok'] and all(r['checks'].values()); assert r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
