from fastapi.testclient import TestClient
from app.main import app
from app.water_sanitation_infrastructure_v43200 import normalize_feature,normalize_system,normalize_series,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/water-sanitation-infrastructure').json();c=client.get('/public/water-sanitation-infrastructure/catalog').json()
 assert o['ok'] and o['version']=='4.35.19' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-water-infrastructure','epa-echo-wastewater','epa-sdwis-drinking-water','who-unicef-jmp-wash'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_facility_equals_operating_utility'] is False and c['truth_boundaries']['wash_estimate_equals_household_service'] is False
def test_empty_state_not_absence_or_water_safety_finding():
 d=client.get('/public/water-sanitation-infrastructure/state').json()
 assert d['evidence']['infrastructure_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_service'] is False and d['truth']['system_record_treated_as_household_water_safety'] is False
def test_osm_feature_not_operation_service_or_water_safety():
 d=normalize_feature({'source_id':'openstreetmap-water-infrastructure','source_url':'https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dwastewater_plant','indicator_type':'wastewater-treatment-plant','evidence_class':'community-mapped-water-infrastructure','source_feature_id':'way-1'})['feature']
 assert d['operating_status_inferred'] is False and d['capacity_inferred'] is False and d['water_safety_inferred'] is False and d['service_area_inferred'] is False
def test_echo_record_not_new_violation_health_or_operation_finding():
 d=normalize_system({'source_id':'epa-echo-wastewater','source_url':'https://echo.epa.gov/tools/web-services','indicator_type':'npdes-regulated-facility','evidence_class':'epa-regulatory-wastewater-record','system_or_facility_id':'NPDES-1','status':'active'})['system']
 assert d['live_operating_status_inferred'] is False and d['new_compliance_finding_inferred'] is False and d['health_risk_inferred'] is False
def test_sdwis_record_not_household_tap_water_safety():
 d=normalize_system({'source_id':'epa-sdwis-drinking-water','source_url':'https://www.epa.gov/enviro/download-additional-envirofacts-datasets','indicator_type':'public-water-system','evidence_class':'epa-drinking-water-system-record','system_or_facility_id':'PWS-1','population_served':12000})['system']
 assert d['household_service_inferred'] is False and d['tap_water_safety_inferred'] is False and d['new_compliance_finding_inferred'] is False
def test_jmp_estimate_not_household_service_or_utility_network_coverage():
 d=normalize_series({'source_id':'who-unicef-jmp-wash','source_url':'https://washdata.org/','indicator_type':'safely-managed-drinking-water','evidence_class':'international-wash-service-estimate','area_code':'KEN','period':'2024','value':62.1,'unit':'percent'})['series']
 assert d['household_level_service_inferred'] is False and d['utility_network_coverage_inferred'] is False and d['real_time_service_inferred'] is False
def test_threshold_preview_is_screening_only():
 d=threshold_preview({'value':48,'threshold':50,'unit':'percent','direction':'below'})['preview']
 assert d['screening_condition_met'] is True and d['service_failure_declared'] is False and d['water_unsafe_declared'] is False and d['regulatory_violation_declared'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/water-sanitation-infrastructure/readiness').json();e=client.get('/public/water-sanitation-infrastructure/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_facility_as_operating_utility'] is False and e['review']['wash_estimate_as_household_service'] is False
