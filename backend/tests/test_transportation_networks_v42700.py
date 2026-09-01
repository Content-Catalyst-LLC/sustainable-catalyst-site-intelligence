from fastapi.testclient import TestClient
from app.main import app
from app.transportation_infrastructure_v42700 import normalize_feature,normalize_feed,accessibility_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/transportation-infrastructure').json();c=client.get('/public/transportation-infrastructure/catalog').json()
 assert o['ok'] and o['version']=='4.39.1' and o['source_count']==4 and o['route']=='earth'
 assert {'overture-transportation','unece-unlocode','ourairports','mobilitydata-database'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['network_segment_equals_navigable_route'] is False
def test_empty_state_not_no_infrastructure_or_navigation():
 d=client.get('/public/transportation-infrastructure/state').json()
 assert d['evidence']['network_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_infrastructure'] is False and d['truth']['platform_navigation_or_safety_determination'] is False
def test_overture_segment_not_navigation_or_legal_access():
 d=normalize_feature({'source_id':'overture-transportation','source_url':'https://docs.overturemaps.org/guides/transportation/','indicator_type':'road-segment','evidence_class':'open-transport-network-feature','source_feature_id':'seg-1','source_class':'primary'})['feature']
 assert d['navigable_route_inferred'] is False and d['legal_access_inferred'] is False and d['safety_inferred'] is False
def test_unlocode_location_not_operating_facility_or_capacity():
 d=normalize_feature({'source_id':'unece-unlocode','source_url':'https://unlocode.unece.org/','indicator_type':'port-location','evidence_class':'unlocode-location-record','source_feature_id':'USCHI','source_status':'function=1'})['feature']
 assert d['operating_status_inferred'] is False and d['capacity_inferred'] is False
def test_ourairports_record_not_official_aeronautical_information():
 d=normalize_feature({'source_id':'ourairports','source_url':'https://ourairports.com/data/','indicator_type':'runway','evidence_class':'community-airport-record','source_feature_id':'KORD-10L-28R'})['feature']
 assert d['safety_inferred'] is False and d['operating_status_inferred'] is False
def test_mobility_feed_not_service_guarantee_or_complete_coverage():
 d=normalize_feed({'source_id':'mobilitydata-database','source_url':'https://mobilitydatabase.org/','indicator_type':'gtfs-schedule-feed','evidence_class':'mobility-feed-catalog-record','feed_id':'mdb-test','service_start':'2026-08-01','service_end':'2026-12-31'})['feed']
 assert d['current_service_inferred'] is False and d['vehicle_arrival_inferred'] is False and d['complete_coverage_inferred'] is False
def test_accessibility_preview_is_screening_not_route_or_service_finding():
 d=accessibility_preview({'network_distance':2.4,'threshold':5,'unit':'km','direction':'within'})['preview']
 assert d['screening_condition_met'] is True and d['actual_travel_time_determined'] is False and d['route_operability_determined'] is False and d['transit_service_determined'] is False and d['navigation_instruction_issued'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/transportation-infrastructure/readiness').json();e=client.get('/public/transportation-infrastructure/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['network_segment_as_navigable_route'] is False and e['review']['platform_navigation_or_safety_determination'] is False
