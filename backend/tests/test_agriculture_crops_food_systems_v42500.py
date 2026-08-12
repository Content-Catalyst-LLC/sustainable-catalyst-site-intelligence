from fastapi.testclient import TestClient
from app.main import app
from app.agriculture_food_systems_v42500 import normalize_measurement,normalize_assessment,threshold_preview
client=TestClient(app)
def test_overview_catalog():
 o=client.get('/public/agriculture-food').json(); c=client.get('/public/agriculture-food/catalog').json()
 assert o['ok'] and o['version']=='4.35.18' and o['source_count']==4
 assert {'faostat','usda-nass-quick-stats','usda-crop-casma','geoglam-crop-monitor'} <= {x['id'] for x in c['sources']}
 assert c['truth_boundaries']['crop_monitor_condition_equals_platform_forecast'] is False
def test_empty_state_no_absence_or_forecast_claim():
 d=client.get('/public/agriculture-food/state').json()
 assert d['evidence']['official_statistic_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_crop_or_no_stress'] is False and d['truth']['crop_monitor_condition_treated_as_platform_forecast'] is False
def test_nass_statistic_not_field_observation_or_exact_count():
 d=normalize_measurement({'source_id':'usda-nass-quick-stats','source_url':'https://quickstats.nass.usda.gov/api','indicator_type':'crop-production','evidence_class':'survey-statistical-estimate','commodity':'CORN','area':'ILLINOIS','year':'2025','value':2250000000,'unit':'BU'})['measurement']
 assert d['field_observation_inferred'] is False and d['exact_count_inferred'] is False and d['production_forecast_inferred'] is False
def test_crop_casma_signal_not_yield_measurement():
 d=normalize_measurement({'source_id':'usda-crop-casma','source_url':'https://nassgeo.csiss.gmu.edu/CropCASMA/','indicator_type':'ndvi','evidence_class':'satellite-derived-condition-index','value':0.63,'unit':'index'})['measurement']
 assert d['yield_measurement_inferred'] is False and d['production_forecast_inferred'] is False
def test_geoglam_assessment_not_platform_forecast():
 d=normalize_assessment({'source_id':'geoglam-crop-monitor','source_url':'https://www.cropmonitor.org/','indicator_type':'crop-condition-assessment','evidence_class':'multi-source-consensus-assessment','commodity':'maize','area':'East Africa','condition':'watch'})['assessment']
 assert d['source_issued_assessment'] is True and d['platform_forecast_inferred'] is False and d['guaranteed_yield_inferred'] is False
def test_faostat_food_balance_not_food_security_determination():
 d=normalize_measurement({'source_id':'faostat','source_url':'https://www.fao.org/faostat/en/','indicator_type':'food-balance-supply','evidence_class':'food-balance-statistical-series','value':2500,'unit':'kcal/capita/day'})['measurement']
 assert d['food_security_determination_inferred'] is False and d['field_observation_inferred'] is False
def test_threshold_is_screening_not_crop_loss_or_food_security():
 d=threshold_preview({'value':0.34,'threshold':0.4,'direction':'below'})['preview']
 assert d['threshold_crossed'] is True and d['crop_loss_determined'] is False and d['production_forecast_issued'] is False and d['food_security_status_determined'] is False
def test_readiness_export():
 r=client.get('/public/agriculture-food/readiness').json(); e=client.get('/public/agriculture-food/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
 assert e['review']['eo_condition_as_yield_measurement'] is False and e['review']['platform_market_advice'] is False
