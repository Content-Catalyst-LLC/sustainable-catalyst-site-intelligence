from fastapi.testclient import TestClient
from app.main import app
from app.energy_systems_v42800 import normalize_feature,normalize_series,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/energy-systems').json();c=client.get('/public/energy-systems/catalog').json()
 assert o['ok'] and o['version']=='4.35.15' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-power','eia-open-data','ember-electricity-data','entsoe-transparency'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_power_feature_equals_energized_asset'] is False
def test_empty_state_not_outage_or_reliability_finding():
 d=client.get('/public/energy-systems/state').json()
 assert d['evidence']['infrastructure_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_energy_infrastructure'] is False and d['truth']['platform_grid_reliability_or_safety_determination'] is False
def test_osm_power_feature_not_energized_operating_or_safe():
 d=normalize_feature({'source_id':'openstreetmap-power','source_url':'https://wiki.openstreetmap.org/wiki/Power','indicator_type':'power-line','evidence_class':'open-power-infrastructure-feature','source_feature_id':'way-1','voltage':'345000'})['feature']
 assert d['energized_status_inferred'] is False and d['operating_status_inferred'] is False and d['safety_clearance_inferred'] is False
def test_eia_capacity_not_realtime_available_capacity_or_local_service():
 d=normalize_series({'source_id':'eia-open-data','source_url':'https://api.eia.gov/v2/','indicator_type':'installed-capacity','evidence_class':'reported-energy-system-series','period':'2026-07','value':1000,'unit':'MW'})['series']
 assert d['real_time_available_capacity_inferred'] is False and d['local_service_status_inferred'] is False
def test_ember_statistics_not_grid_telemetry_or_service_status():
 d=normalize_series({'source_id':'ember-electricity-data','source_url':'https://api.ember-energy.org/v1/','indicator_type':'electricity-generation','evidence_class':'harmonized-electricity-statistic','period':'2026-06','value':42,'unit':'TWh'})['series']
 assert d['grid_reliability_inferred'] is False and d['local_service_status_inferred'] is False
def test_entsoe_forecast_not_observation_or_outage_declaration():
 d=normalize_series({'source_id':'entsoe-transparency','source_url':'https://web-api.tp.entsoe.eu/api','indicator_type':'load-forecast','evidence_class':'transparency-platform-market-system-record','period':'2026-08-11T00:00Z','value':50000,'unit':'MW','is_forecast':True})['series']
 assert d['is_forecast'] is True and d['forecast_treated_as_observation'] is False and d['grid_reliability_inferred'] is False
def test_threshold_preview_is_screening_not_grid_emergency():
 d=threshold_preview({'value':98,'threshold':95,'unit':'percent','direction':'above'})['preview']
 assert d['screening_condition_met'] is True and d['outage_declared'] is False and d['reliability_violation_determined'] is False and d['grid_emergency_determined'] is False and d['equipment_safety_determined'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/energy-systems/readiness').json();e=client.get('/public/energy-systems/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_feature_as_energized_asset'] is False and e['review']['platform_grid_reliability_or_safety_determination'] is False
