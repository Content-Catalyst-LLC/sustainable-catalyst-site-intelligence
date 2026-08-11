from fastapi.testclient import TestClient
from app.main import app
from app.solid_waste_circular_materials_v43300 import normalize_feature,normalize_regulatory,normalize_series,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/solid-waste-circular-materials').json();c=client.get('/public/solid-waste-circular-materials/catalog').json()
 assert o['ok'] and o['version']=='4.35.0' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-waste-recycling','epa-rcrainfo-hazardous-waste','world-bank-what-a-waste','eurostat-waste'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_waste_feature_equals_operating_facility'] is False and c['truth_boundaries']['reported_recycling_rate_equals_material_circularity'] is False
def test_empty_state_not_absence_or_operation_finding():
 d=client.get('/public/solid-waste-circular-materials/state').json()
 assert d['evidence']['waste_infrastructure_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_waste_infrastructure'] is False and d['truth']['mapped_feature_treated_as_operating_facility'] is False
def test_osm_feature_not_operation_permission_capacity_or_compliance():
 d=normalize_feature({'source_id':'openstreetmap-waste-recycling','source_url':'https://wiki.openstreetmap.org/wiki/Tag:amenity%3Drecycling','indicator_type':'recycling-centre','evidence_class':'community-mapped-waste-infrastructure','source_feature_id':'node-1'})['feature']
 assert d['operating_status_inferred'] is False and d['permitted_status_inferred'] is False and d['remaining_capacity_inferred'] is False and d['compliance_inferred'] is False
def test_epa_record_not_live_inventory_new_violation_or_health_finding():
 d=normalize_regulatory({'source_id':'epa-rcrainfo-hazardous-waste','source_url':'https://echo.epa.gov/tools/web-services','indicator_type':'hazardous-waste-handler','evidence_class':'epa-hazardous-waste-regulatory-record','facility_id':'RCRA-1','source_status':'active'})['regulatory_record']
 assert d['live_operating_status_inferred'] is False and d['live_material_inventory_inferred'] is False and d['new_compliance_finding_inferred'] is False and d['exposure_or_health_risk_inferred'] is False
def test_world_bank_waste_statistic_not_household_or_facility_outcome():
 d=normalize_series({'source_id':'world-bank-what-a-waste','source_url':'https://datacatalog.worldbank.org/search/dataset/0039597/what-a-waste-global-database','indicator_type':'municipal-waste-generation','evidence_class':'global-waste-system-statistic','area_code':'KEN','period':'2025','value':5.1,'unit':'million-tonnes','value_kind':'estimated'})['series']
 assert d['facility_level_outcome_inferred'] is False and d['household_level_outcome_inferred'] is False and d['actual_material_recovery_inferred'] is False and d['circularity_inferred'] is False
def test_projection_retains_projection_truth_boundary():
 d=normalize_series({'source_id':'world-bank-what-a-waste','source_url':'https://datacatalog.worldbank.org/search/dataset/0039597/what-a-waste-global-database','indicator_type':'municipal-waste-generation','evidence_class':'global-waste-system-statistic','area_code':'GLOBAL','period':'2050','value':3.8,'unit':'billion-tonnes','value_kind':'projected'})['series']
 assert d['value_kind']=='projected' and d['projection_treated_as_observation'] is False
def test_eurostat_recycling_rate_not_material_circularity_certification():
 d=normalize_series({'source_id':'eurostat-waste','source_url':'https://ec.europa.eu/eurostat/web/waste','indicator_type':'municipal-waste-recycling-rate','evidence_class':'official-european-waste-statistic','area_code':'EU27_2020','period':'2024','value':49.0,'unit':'percent','value_kind':'reported'})['series']
 assert d['actual_material_recovery_inferred'] is False and d['circularity_inferred'] is False and d['compliance_inferred'] is False
def test_threshold_and_export_are_screening_only():
 p=threshold_preview({'value':55,'threshold':50,'unit':'percent','direction':'above'})['preview'];e=client.get('/public/solid-waste-circular-materials/export-manifest').json();r=client.get('/public/solid-waste-circular-materials/readiness').json()
 assert p['screening_condition_met'] is True and p['waste_crisis_declared'] is False and p['recycling_success_declared'] is False and p['circularity_declared'] is False
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_feature_as_operating_facility'] is False and e['review']['recycling_rate_as_material_circularity'] is False
