from fastapi.testclient import TestClient
from app.main import app
from app.biodiversity_intelligence_v42300 import normalize_occurrence, normalize_conservation, overlap_preview
client=TestClient(app)
def test_overview_and_catalog():
    o=client.get('/public/biodiversity').json(); c=client.get('/public/biodiversity/catalog').json()
    assert o['ok'] and o['version']=='4.35.11' and o['contract']=='global-biodiversity-species-distribution-conservation-intelligence'
    assert o['source_count']==4 and c['truth_boundaries']['zero_records_equals_absence'] is False
    assert {'gbif-occurrence','obis','ebird-public','usfws-ecos'} <= {x['id'] for x in c['sources']}
def test_empty_state_has_no_absence_or_population_claim():
    d=client.get('/public/biodiversity/state',params={'source':'gbif-occurrence','indicator_type':'species-occurrence','scientific_name':'Danaus plexippus'}).json()
    assert d['ok'] and d['evidence']['occurrence_record_loaded'] is False
    assert d['truth']['zero_records_treated_as_absence'] is False and d['truth']['occurrence_treated_as_population'] is False
def test_gbif_occurrence_not_population_or_current_occupancy():
    d=normalize_occurrence({'source_id':'gbif-occurrence','source_url':'https://api.gbif.org/v1/occurrence/123','indicator_type':'species-occurrence','evidence_class':'occurrence-record','scientific_name':'Danaus plexippus','event_date':'2026-07-01','latitude':41.88,'longitude':-87.63})['occurrence']
    assert d['occurrence_treated_as_population'] is False and d['observation_treated_as_current_occupancy'] is False and d['survey_completeness_verified'] is False
def test_obis_zero_results_never_become_absence():
    d=client.get('/public/biodiversity/state',params={'source':'obis','indicator_type':'marine-species-occurrence'}).json()
    assert d['truth']['zero_records_treated_as_absence'] is False and d['evidence']['survey_completeness_verified'] is False
def test_ebird_observation_not_breeding_confirmation():
    d=client.get('/public/biodiversity/state',params={'source':'ebird-public','indicator_type':'bird-observation'}).json()
    assert d['truth']['bird_observation_treated_as_breeding_confirmation'] is False and d['truth']['aggregate_count_treated_as_abundance'] is False
def test_usfws_status_is_not_global_status_or_project_effect():
    d=normalize_conservation({'source_id':'usfws-ecos','source_url':'https://ecos.fws.gov/ecp/services','indicator_type':'esa-listing-status','evidence_class':'esa-species-record','scientific_name':'Myotis sodalis','source_status':'Endangered'})['conservation']
    assert d['jurisdiction']=='United States' and d['global_conservation_status_inferred'] is False and d['project_effect_determined'] is False and d['platform_legal_determination'] is False
def test_overlap_is_spatial_orientation_not_legal_finding():
    d=overlap_preview({'record_bbox':[-88,41,-87,42],'area_bbox':[-87.9,41.1,-87.2,41.8]})['preview']
    assert d['spatial_overlap'] is True and d['species_presence_verified'] is False and d['project_effect_determined'] is False and d['legal_determination'] is False
def test_readiness_and_export_preserve_truth_boundaries():
    r=client.get('/public/biodiversity/readiness').json(); e=client.get('/public/biodiversity/export-manifest').json()
    assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta']==0
    assert e['review']['zero_records_as_absence'] is False and e['review']['critical_habitat_overlap_as_project_effect'] is False
