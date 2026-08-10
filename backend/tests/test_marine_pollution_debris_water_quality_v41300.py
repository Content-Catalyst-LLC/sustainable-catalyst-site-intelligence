from fastapi.testclient import TestClient

from app.main import app
from app.marine_pollution_v41300 import export_manifest, normalize_debris, normalize_measurement, readiness, threshold_preview

CLIENT = TestClient(app)


def test_overview_and_catalog_register_four_source_families():
    o = CLIENT.get('/public/marine-pollution').json()
    assert o['ok'] and o['version'] == '4.28.0'
    assert o['contract'] == 'marine-pollution-debris-water-quality'
    c = CLIENT.get('/public/marine-pollution/catalog').json()
    assert {x['id'] for x in c['sources']} == {
        'noaa-ncei-marine-microplastics','emodnet-chemistry','copernicus-marine-biogeochemistry','water-quality-portal'
    }
    assert {'microplastics','seafloor-litter','heavy-metals','nutrients','dissolved-oxygen','ph-acidity'} <= {x['id'] for x in c['indicator_types']}


def test_state_starts_without_pollution_or_health_claims():
    p = CLIENT.get('/public/marine-pollution/state?source=emodnet-chemistry&indicator_type=heavy-metals&latitude=54.0&longitude=5.0&date=2026-08-09').json()
    assert p['source_supports_indicator_type'] is True
    assert p['evidence']['measurement_loaded'] is False
    assert p['truth']['zero_records_treated_as_clean_water'] is False
    assert p['truth']['non_detect_treated_as_zero'] is False
    assert p['truth']['platform_health_risk_finding'] is False
    assert p['truth']['platform_compliance_finding'] is False


def test_non_detect_normalization_does_not_become_zero():
    p = normalize_measurement({
        'source_id':'water-quality-portal',
        'source_url':'https://www.waterqualitydata.us/',
        'indicator_type':'heavy-metals',
        'evidence_class':'non-detect',
        'record_id':'wqp-example',
        'latitude':41.88,'longitude':-87.60,
        'sampled_at':'2026-08-09T12:00:00Z',
        'value':None,'unit':'ug/L','detection_limit':0.5,'qualifier':'non-detect','matrix':'water'
    })
    m = p['measurement']
    assert m['source_non_detect'] is True
    assert m['value'] is None
    assert m['non_detect_interpreted_as_zero'] is False
    assert m['health_risk_inferred'] is False
    assert m['regulatory_compliance_inferred'] is False
    assert len(p['measurement_sha256']) == 64


def test_model_analysis_remains_distinct_from_in_situ_sample():
    p = normalize_measurement({
        'source_id':'copernicus-marine-biogeochemistry',
        'source_url':'https://data.marine.copernicus.eu/',
        'indicator_type':'ph-acidity',
        'evidence_class':'biogeochemical-analysis',
        'bbox':[-10,40,-9,41],
        'sampled_at':'2026-08-09T00:00:00Z',
        'value':8.05,'unit':'1','matrix':'model-grid'
    })
    assert p['measurement']['evidence_class'] == 'biogeochemical-analysis'
    assert p['measurement']['model_treated_as_in_situ'] is False


def test_debris_observation_does_not_attribute_source_actor_or_pathway():
    p = normalize_debris({
        'source_id':'emodnet-chemistry',
        'source_url':'https://emodnet.ec.europa.eu/en/chemistry',
        'indicator_type':'seafloor-litter',
        'evidence_class':'marine-litter-observation',
        'record_id':'emodnet-litter-example','bbox':[2,50,3,51],
        'observed_at':'2026-08-09','count':12,'unit':'items/km2','matrix':'seafloor'
    })
    d = p['debris']
    assert d['source_actor_attributed_by_platform'] is False
    assert d['transport_pathway_inferred_by_platform'] is False
    assert d['ecological_harm_inferred'] is False
    assert len(p['debris_sha256']) == 64


def test_threshold_preview_is_orientation_not_regulatory_or_health_finding():
    p = threshold_preview({'measurement_value':12,'threshold_value':10,'measurement_unit':'ug/L','threshold_unit':'ug/L','direction':'above'})
    assert p['preview']['orientation_condition_met'] is True
    assert p['preview']['regulatory_exceedance'] is False
    assert p['preview']['health_advisory'] is False
    assert p['preview']['human_exposure_established'] is False
    assert p['preview']['ecological_harm_concluded'] is False


def test_bad_source_host_and_cross_source_indicator_are_rejected():
    bad = CLIENT.post('/public/marine-pollution/measurement/normalize', json={
        'source_id':'noaa-ncei-marine-microplastics','source_url':'https://example.com/',
        'indicator_type':'microplastics','evidence_class':'microplastics-observation','latitude':1,'longitude':1
    })
    assert bad.status_code == 400
    wrong = CLIENT.get('/public/marine-pollution/state?source=noaa-ncei-marine-microplastics&indicator_type=heavy-metals').json()
    assert wrong['source_supports_indicator_type'] is False


def test_manifest_and_readiness_preserve_truth_boundaries_and_route_count():
    p = export_manifest('noaa-ncei-marine-microplastics','microplastics',0,0,'2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-marine-pollution/1.0'
    assert p['review']['zero_records_as_clean_water'] is False
    assert p['review']['non_detect_as_zero'] is False
    assert p['review']['threshold_as_regulatory_or_health_finding'] is False
    assert p['review']['platform_compliance_finding'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
