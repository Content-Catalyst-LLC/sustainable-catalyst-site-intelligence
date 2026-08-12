from fastapi.testclient import TestClient
from app.main import app
from app.industrial_manufacturing_trade_v43000 import normalize_feature,normalize_series,normalize_trade_flow,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/industrial-manufacturing').json();c=client.get('/public/industrial-manufacturing/catalog').json()
 assert o['ok'] and o['version']=='4.35.18' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-industrial','world-bank-manufacturing','world-bank-gem','world-bank-wits-trade'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_industrial_feature_equals_operating_facility'] is False and c['truth_boundaries']['bilateral_trade_equals_supply_chain_dependency'] is False
def test_empty_state_not_disruption_or_absence_finding():
 d=client.get('/public/industrial-manufacturing/state').json()
 assert d['evidence']['industrial_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_industry_or_trade'] is False and d['truth']['platform_disruption_or_shortage_determination'] is False
def test_osm_industrial_feature_not_operation_output_or_regulatory_status():
 d=normalize_feature({'source_id':'openstreetmap-industrial','source_url':'https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dworks','indicator_type':'factory-works','evidence_class':'community-mapped-industrial-feature','source_feature_id':'way-1'})['feature']
 assert d['operating_status_inferred'] is False and d['production_volume_inferred'] is False and d['regulatory_status_inferred'] is False
def test_world_bank_manufacturing_statistic_not_facility_output():
 d=normalize_series({'source_id':'world-bank-manufacturing','source_url':'https://data.worldbank.org/indicator/NV.IND.MANF.ZS','indicator_type':'manufacturing-share-gdp','evidence_class':'harmonized-national-manufacturing-statistic','period':'2025','value':12.5,'unit':'percent'})['series']
 assert d['facility_output_inferred'] is False and d['plant_utilization_inferred'] is False and d['real_time_production_inferred'] is False
def test_gem_industrial_series_not_plant_telemetry_or_disruption():
 d=normalize_series({'source_id':'world-bank-gem','source_url':'https://datacatalog.worldbank.org/search/dataset/0037798/global-economic-monitor','indicator_type':'industrial-production-index','evidence_class':'high-frequency-industrial-trade-series','period':'2026-06','value':101.2,'unit':'index'})['series']
 assert d['real_time_production_inferred'] is False and d['disruption_inferred'] is False and d['shortage_inferred'] is False
def test_wits_trade_record_not_shipment_or_dependency():
 d=normalize_trade_flow({'source_id':'world-bank-wits-trade','source_url':'https://datacatalog.worldbank.org/search/dataset/0039685/world-integrated-trade-solution-trade-stats','indicator_type':'bilateral-export-value','evidence_class':'aggregated-bilateral-trade-statistic','period':'2024','reporter':'USA','partner':'MEX','product_group':'84-85','value':100,'unit':'USD million'})['trade_flow']
 assert d['physical_shipment_inferred'] is False and d['shipment_route_inferred'] is False and d['supplier_dependency_inferred'] is False and d['inventory_position_inferred'] is False
def test_threshold_preview_is_screening_not_disruption_or_shortage():
 d=threshold_preview({'value':8,'threshold':10,'unit':'index','direction':'below'})['preview']
 assert d['screening_condition_met'] is True and d['disruption_declared'] is False and d['shortage_determined'] is False and d['supply_chain_dependency_determined'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/industrial-manufacturing/readiness').json();e=client.get('/public/industrial-manufacturing/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_feature_as_operating_facility'] is False and e['review']['bilateral_trade_as_supply_chain_dependency'] is False
