from fastapi.testclient import TestClient
from app.main import app
from app.wetlands_inland_waters_v42400 import normalize_feature,normalize_measurement,overlap_preview
client=TestClient(app)
def test_overview_catalog():
 o=client.get('/public/wetlands-inland-water').json(); c=client.get('/public/wetlands-inland-water/catalog').json()
 assert o['ok'] and o['version']=='4.33.0' and o['source_count']==4
 assert {'usfws-nwi','ramsar-rsis','jrc-global-surface-water','nasa-swot-inland-water'} <= {x['id'] for x in c['sources']}
 assert c['truth_boundaries']['mapped_wetland_equals_jurisdictional_wetland'] is False
def test_empty_state_no_absence_or_jurisdiction_claim():
 d=client.get('/public/wetlands-inland-water/state').json(); assert d['evidence']['wetland_feature_loaded'] is False
 assert d['truth']['zero_records_treated_as_no_wetland_or_habitat'] is False and d['truth']['platform_permitting_determination'] is False
def test_nwi_feature_not_jurisdictional_delineation():
 d=normalize_feature({'source_id':'usfws-nwi','source_url':'https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest','indicator_type':'wetland-classification','evidence_class':'wetland-inventory-feature','source_class':'PEM1A'})['feature']
 assert d['jurisdictional_wetland_inferred'] is False and d['permitting_status_inferred'] is False and d['wetland_absence_inferred'] is False
def test_ramsar_not_complete_wetland_inventory():
 d=client.get('/public/wetlands-inland-water/state',params={'source':'ramsar-rsis','indicator_type':'ramsar-site'}).json()
 assert d['truth']['ramsar_site_treated_as_complete_inventory'] is False and d['truth']['zero_records_treated_as_no_wetland_or_habitat'] is False
def test_jrc_surface_water_not_wetland_type_or_harm():
 d=client.get('/public/wetlands-inland-water/state',params={'source':'jrc-global-surface-water','indicator_type':'surface-water-transition'}).json()
 assert d['truth']['surface_water_treated_as_wetland_type'] is False and d['truth']['surface_water_change_treated_as_ecological_harm'] is False
def test_swot_measurement_not_field_gauge_or_warning():
 d=normalize_measurement({'source_id':'nasa-swot-inland-water','source_url':'https://gis.earthdata.nasa.gov/','indicator_type':'water-surface-elevation','evidence_class':'swot-radar-measurement','value':122.4,'unit':'m'})['measurement']
 assert d['field_gauge_inferred'] is False and d['flood_warning_inferred'] is False and d['navigational_safety_inferred'] is False
def test_overlap_is_orientation_not_permitting_finding():
 d=overlap_preview({'feature_bbox':[-88,41,-87,42],'area_bbox':[-87.9,41.1,-87.2,41.8]})['preview']
 assert d['spatial_overlap'] is True and d['jurisdictional_status_determined'] is False and d['permit_requirement_determined'] is False and d['legal_determination'] is False
def test_readiness_export():
 r=client.get('/public/wetlands-inland-water/readiness').json(); e=client.get('/public/wetlands-inland-water/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
 assert e['review']['mapped_wetland_as_jurisdictional'] is False and e['review']['platform_flood_warning'] is False
