from fastapi.testclient import TestClient
from app.main import app
from app.mining_critical_materials_v43100 import normalize_feature,normalize_resource,normalize_series,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/mining-critical-materials').json();c=client.get('/public/mining-critical-materials/catalog').json()
 assert o['ok'] and o['version']=='4.35.5' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-mining','usgs-usmin','usgs-mcs-2026','iea-critical-minerals'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_mining_feature_equals_operating_mine'] is False and c['truth_boundaries']['scenario_gap_equals_shortage'] is False
def test_empty_state_not_absence_or_supply_finding():
 d=client.get('/public/mining-critical-materials/state').json()
 assert d['evidence']['mining_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_mineral_resource'] is False and d['truth']['critical_label_treated_as_investment_or_security_determination'] is False
def test_osm_mining_feature_not_operation_or_reserve():
 d=normalize_feature({'source_id':'openstreetmap-mining','source_url':'https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dquarry','indicator_type':'quarry','evidence_class':'community-mapped-mining-feature','source_feature_id':'way-1'})['feature']
 assert d['operating_status_inferred'] is False and d['production_inferred'] is False and d['reserve_inferred'] is False and d['permit_status_inferred'] is False
def test_usmin_resource_not_certified_reserve_or_operating_status():
 d=normalize_resource({'source_id':'usgs-usmin','source_url':'https://www.usgs.gov/centers/gggsc/science/usmin-mineral-deposit-database','indicator_type':'reported-resource','evidence_class':'authoritative-us-mineral-deposit-record','commodity':'lithium','classification':'reported resource','value':1.2,'unit':'Mt'})['resource']
 assert d['certified_reserve_inferred'] is False and d['economic_recoverability_inferred'] is False and d['mine_operating_status_inferred'] is False
def test_mcs_production_not_mine_output_or_live_status():
 d=normalize_series({'source_id':'usgs-mcs-2026','source_url':'https://pubs.usgs.gov/publication/mcs2026','indicator_type':'world-mine-production','evidence_class':'official-mineral-commodity-statistic','commodity':'copper','period':'2025','value':23.0,'unit':'Mt'})['series']
 assert d['mine_level_output_inferred'] is False and d['live_operating_status_inferred'] is False and d['shortage_inferred'] is False
def test_iea_projection_not_observation_shortage_or_investment_recommendation():
 d=normalize_series({'source_id':'iea-critical-minerals','source_url':'https://www.iea.org/data-and-statistics/data-tools/critical-minerals-data-explorer','indicator_type':'projected-total-demand','evidence_class':'scenario-based-critical-mineral-projection','commodity':'lithium','period':'2040','scenario':'STEPS','value':2.0,'unit':'Mt'})['series']
 assert d['guaranteed_forecast_inferred'] is False and d['shortage_inferred'] is False and d['investment_recommendation_inferred'] is False and d['security_finding_inferred'] is False
def test_threshold_preview_is_screening_not_shortage_or_reserve_certification():
 d=threshold_preview({'value':8,'threshold':10,'unit':'index','direction':'below'})['preview']
 assert d['screening_condition_met'] is True and d['shortage_declared'] is False and d['reserve_certified'] is False and d['investment_recommendation_issued'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/mining-critical-materials/readiness').json();e=client.get('/public/mining-critical-materials/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_feature_as_operating_mine'] is False and e['review']['scenario_gap_as_shortage'] is False
