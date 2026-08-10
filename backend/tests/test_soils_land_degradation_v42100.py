from fastapi.testclient import TestClient
from app.main import app
from app.soils_land_degradation_v42100 import normalize_measurement, normalize_assessment, threshold_preview
client=TestClient(app)
def test_overview_and_catalog():
    o=client.get('/public/soils-land').json(); c=client.get('/public/soils-land/catalog').json()
    assert o['ok'] and o['version']=='4.24.0' and o['contract']=='global-soils-land-degradation-desertification-intelligence'
    assert o['source_count']==4 and c['truth_boundaries']['soilgrids_equals_ground_sample'] is False
    assert {'isric-soilgrids','usda-nrcs-soil-data-access','nasa-smap-soil-moisture','unccd-land-degradation'} <= {x['id'] for x in c['sources']}
def test_empty_state_has_no_soil_health_claim():
    d=client.get('/public/soils-land/state',params={'source':'isric-soilgrids','indicator_type':'soil-organic-carbon'}).json()
    assert d['ok'] and d['evidence']['soil_property_loaded'] is False
    assert d['truth']['soilgrids_treated_as_ground_sample'] is False
    assert d['truth']['zero_records_treated_as_healthy_soil'] is False
def test_soilgrids_prediction_not_ground_sample():
    d=normalize_measurement({'source_id':'isric-soilgrids','source_url':'https://rest.isric.org/soilgrids/v2.0/properties/query','indicator_type':'soil-organic-carbon','evidence_class':'modelled-soil-property-map','value':32.0,'unit':'dg/kg','depth_interval':'0-5cm','uncertainty':8.0})['measurement']
    assert d['modelled_map_treated_as_ground_sample'] is False and d['platform_determination_issued'] is False
def test_usda_mapunit_not_parcel_truth():
    d=normalize_measurement({'source_id':'usda-nrcs-soil-data-access','source_url':'https://sdmdataaccess.nrcs.usda.gov/','indicator_type':'hydrologic-soil-group','evidence_class':'official-soil-survey-mapunit'})['measurement']
    assert d['mapunit_treated_as_parcel_truth'] is False
def test_smap_l4_not_direct_observation():
    d=normalize_measurement({'source_id':'nasa-smap-soil-moisture','source_url':'https://nsidc.org/data/spl4smgp/versions/8','indicator_type':'root-zone-soil-moisture','evidence_class':'model-assimilated-soil-moisture','value':0.31,'unit':'m3/m3','processing_level':'L4'})['measurement']
    assert d['model_assimilation_treated_as_direct_observation'] is False
def test_unccd_assessment_preserves_reporting_context():
    d=normalize_assessment({'source_id':'unccd-land-degradation','source_url':'https://data.unccd.int/land-degradation','indicator_type':'land-degradation-proportion','evidence_class':'country-reported-land-degradation-indicator','reporting_entity':'Example Party','reporting_period':'2016-2019','value':12.5,'unit':'percent'})['assessment']
    assert d['country_reported'] is True and d['comprehensive_global_assessment'] is False and d['causal_attribution'] is False
def test_threshold_preview_no_degradation_or_carbon_finding():
    p=threshold_preview({'value':18.0,'threshold':15.0,'operator':'>=','unit':'percent'})['preview']
    assert p['comparison'] is True and p['land_degradation_declaration'] is False and p['desertification_declaration'] is False and p['carbon_credit_finding'] is False
def test_readiness_and_export():
    r=client.get('/public/soils-land/readiness').json(); e=client.get('/public/soils-land/export-manifest').json()
    assert r['ok'] and all(r['checks'].values()) and e['review']['soilgrids_as_ground_sample'] is False and e['review']['soil_carbon_as_carbon_credit'] is False
