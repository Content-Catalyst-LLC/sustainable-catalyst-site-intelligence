from fastapi.testclient import TestClient
from app.main import app
from app.digital_connectivity_v42900 import normalize_feature,normalize_measurement,normalize_availability,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/digital-connectivity').json();c=client.get('/public/digital-connectivity/catalog').json()
 assert o['ok'] and o['version']=='4.36.1' and o['source_count']==4 and o['route']=='earth'
 assert {'openstreetmap-telecom','mlab-network-performance','world-bank-connectivity','fcc-broadband-data'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_telecom_feature_equals_coverage_or_operating_asset'] is False
def test_empty_state_not_outage_or_absence_finding():
 d=client.get('/public/digital-connectivity/state').json()
 assert d['evidence']['telecom_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_connectivity'] is False and d['truth']['platform_outage_or_coverage_determination'] is False
def test_osm_feature_not_coverage_operation_or_service():
 d=normalize_feature({'source_id':'openstreetmap-telecom','source_url':'https://wiki.openstreetmap.org/wiki/Key:communication','indicator_type':'communications-tower','evidence_class':'community-mapped-telecom-feature','source_feature_id':'node-1'})['feature']
 assert d['coverage_inferred'] is False and d['operating_status_inferred'] is False and d['service_availability_inferred'] is False
def test_mlab_measurement_not_universal_provider_performance_or_outage():
 d=normalize_measurement({'source_id':'mlab-network-performance','source_url':'https://www.measurementlab.net/data/','indicator_type':'download-throughput','evidence_class':'client-initiated-network-measurement','period':'2026-08-10','value':120,'unit':'Mbps','sample_count':55})['measurement']
 assert d['universal_local_performance_inferred'] is False and d['provider_compliance_inferred'] is False and d['outage_inferred'] is False
def test_world_bank_statistic_not_household_access_or_coverage():
 d=normalize_measurement({'source_id':'world-bank-connectivity','source_url':'https://data.worldbank.org/indicator/IT.NET.USER.ZS','indicator_type':'internet-users-share','evidence_class':'harmonized-national-connectivity-statistic','period':'2025','value':90,'unit':'percent'})['measurement']
 assert d['universal_local_performance_inferred'] is False and d['service_availability_inferred'] is False
def test_fcc_availability_not_measured_performance_or_guaranteed_install():
 d=normalize_availability({'source_id':'fcc-broadband-data','source_url':'https://broadbandmap.fcc.gov/data-download','indicator_type':'fixed-broadband-availability','evidence_class':'provider-reported-broadband-availability','as_of':'2026-06-30','advertised_download_mbps':1000})['availability']
 assert d['measured_performance_inferred'] is False and d['guaranteed_installability_inferred'] is False and d['current_operating_status_inferred'] is False
def test_threshold_preview_is_screening_not_outage_or_coverage_failure():
 d=threshold_preview({'value':15,'threshold':25,'unit':'Mbps','direction':'below'})['preview']
 assert d['screening_condition_met'] is True and d['outage_declared'] is False and d['coverage_failure_determined'] is False and d['network_safety_determined'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/digital-connectivity/readiness').json();e=client.get('/public/digital-connectivity/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['mapped_feature_as_coverage_or_operating_asset'] is False and e['review']['platform_outage_or_coverage_determination'] is False
