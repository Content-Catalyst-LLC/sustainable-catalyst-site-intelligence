from fastapi.testclient import TestClient
from app.main import app
from app.human_settlements_v42600 import SOURCES,normalize_measurement,normalize_feature,threshold_preview
client=TestClient(app)
def test_source_registry_and_truth_boundary():
 o=client.get('/public/human-settlements').json();c=client.get('/public/human-settlements/catalog').json()
 assert o['ok'] and o['version']=='4.36.1' and o['source_count']==4 and o['route']=='earth'
 assert {'jrc-ghsl','worldpop-global2','nasa-black-marble','world-bank-urban'}<={x['id'] for x in c['sources']}
 assert c['truth_boundaries']['population_estimate_equals_census_headcount'] is False
def test_empty_state_not_uninhabited_or_property_determination():
 d=client.get('/public/human-settlements/state').json()
 assert d['evidence']['built_environment_grid_loaded'] is False
 assert d['truth']['zero_records_treated_as_uninhabited'] is False and d['truth']['platform_zoning_or_property_determination'] is False
def test_ghsl_feature_not_parcel_or_direct_epoch_observation():
 d=normalize_feature({'source_id':'jrc-ghsl','source_url':'https://human-settlement.emergency.copernicus.eu/','indicator_type':'settlement-class','evidence_class':'ghsl-settlement-model','epoch':'2030','processing_status':'modeled-extrapolated','source_class':'urban-centre'})['feature']
 assert d['parcel_building_footprint_inferred'] is False and d['direct_observation_for_epoch_inferred'] is False and d['zoning_status_inferred'] is False
def test_worldpop_estimate_not_census_or_occupancy():
 d=normalize_measurement({'source_id':'worldpop-global2','source_url':'https://api.worldpop.org/v2/','indicator_type':'population-estimate','evidence_class':'modeled-population-surface','value':125432.67,'unit':'people','year':'2026','resolution':'100m'})['measurement']
 assert d['census_headcount_inferred'] is False and d['building_occupancy_inferred'] is False
def test_black_marble_radiance_not_power_economy_or_population():
 d=normalize_measurement({'source_id':'nasa-black-marble','source_url':'https://cmr.earthdata.nasa.gov/search/granules.json','indicator_type':'nighttime-radiance','evidence_class':'satellite-nighttime-radiance','value':18.4,'unit':'nW/cm2/sr','quality_flag':'good'})['measurement']
 assert d['electricity_service_inferred'] is False and d['economic_output_inferred'] is False and d['infrastructure_functionality_inferred'] is False
def test_world_bank_urban_indicator_not_settlement_boundary():
 d=normalize_measurement({'source_id':'world-bank-urban','source_url':'https://api.worldbank.org/v2/','indicator_type':'urban-population-share','evidence_class':'harmonized-urban-indicator-series','value':83.1,'unit':'percent','year':'2025'})['measurement']
 assert d['census_headcount_inferred'] is False and d['building_occupancy_inferred'] is False
def test_threshold_is_screening_not_zoning_or_service_finding():
 d=threshold_preview({'value':0.72,'threshold':0.6,'direction':'above'})['preview']
 assert d['threshold_crossed'] is True and d['urban_status_determined'] is False and d['infrastructure_service_determined'] is False and d['zoning_determined'] is False
def test_readiness_export_preserve_architecture():
 r=client.get('/public/human-settlements/readiness').json();e=client.get('/public/human-settlements/export-manifest').json()
 assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0 and r['summary']['primary_area_count_delta']==0
 assert e['review']['population_estimate_as_census'] is False and e['review']['platform_zoning_or_property_determination'] is False
