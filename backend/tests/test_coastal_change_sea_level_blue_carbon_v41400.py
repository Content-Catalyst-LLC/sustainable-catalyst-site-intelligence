from fastapi.testclient import TestClient

from app.main import app
from app.coastal_change_v41400 import export_manifest, normalize_habitat, normalize_shoreline, normalize_water_level, readiness, scenario_preview

CLIENT = TestClient(app)


def test_overview_and_catalog_register_four_coastal_source_families():
    o = CLIENT.get('/public/coastal-change').json()
    assert o['ok'] and o['version'] == '4.37.0'
    assert o['contract'] == 'coastal-change-sea-level-blue-carbon'
    c = CLIENT.get('/public/coastal-change/catalog').json()
    assert {x['id'] for x in c['sources']} == {'noaa-coops','noaa-digital-coast','usgs-coastal-change','global-mangrove-watch'}
    assert {'observed-water-level','sea-level-scenario','shoreline-change','tidal-wetland','mangrove-extent','blue-carbon-habitat'} <= {x['id'] for x in c['indicator_types']}


def test_state_starts_without_forecast_property_or_carbon_claims():
    p = CLIENT.get('/public/coastal-change/state?source=noaa-digital-coast&indicator_type=sea-level-scenario&latitude=29.0&longitude=-90.0&date=2026-08-09').json()
    assert p['source_supports_indicator_type'] is True
    assert p['evidence']['scenario_layer_loaded'] is False
    assert p['truth']['scenario_treated_as_exact_flood_forecast'] is False
    assert p['truth']['platform_property_loss_finding'] is False
    assert p['truth']['habitat_treated_as_carbon_credit'] is False


def test_tide_prediction_remains_prediction_and_datum_is_preserved():
    p = normalize_water_level({
        'source_id':'noaa-coops','source_url':'https://api.tidesandcurrents.noaa.gov/api/prod/',
        'indicator_type':'tide-prediction','evidence_class':'tide-prediction','station_id':'8518750',
        'latitude':40.7,'longitude':-74.0,'observed_or_predicted_at':'2026-08-10T00:00:00Z',
        'value':1.23,'unit':'m','vertical_datum':'MLLW'
    })
    r = p['water_level']
    assert r['evidence_class'] == 'tide-prediction'
    assert r['vertical_datum'] == 'MLLW'
    assert r['prediction_treated_as_observation'] is False
    assert r['total_water_level_inferred'] is False
    assert r['flooding_inferred'] is False


def test_shoreline_change_preserves_uncertainty_and_no_property_inference():
    p = normalize_shoreline({
        'source_id':'usgs-coastal-change','source_url':'https://marine.usgs.gov/coastalchangehazardsportal/',
        'indicator_type':'shoreline-change','evidence_class':'shoreline-analysis','record_id':'usgs-example',
        'bbox':[-75,35,-74,36],'analysis_period':'1980-2020','rate':-0.7,'rate_unit':'m/year','uncertainty':0.2
    })
    r = p['shoreline']
    assert r['rate'] == -0.7 and r['uncertainty'] == 0.2
    assert r['future_position_guaranteed'] is False
    assert r['property_loss_inferred'] is False
    assert r['safety_finding'] is False


def test_habitat_record_never_becomes_platform_carbon_credit_claim():
    p = normalize_habitat({
        'source_id':'global-mangrove-watch','source_url':'https://www.globalmangrovewatch.org/',
        'indicator_type':'mangrove-extent','evidence_class':'habitat-layer','record_id':'gmw-example',
        'bbox':[39,-5,40,-4],'observed_at':'2025','area':125.0,'area_unit':'km2','classification':'mangrove'
    })
    r = p['habitat']
    assert r['carbon_stock_derived_by_platform'] is False
    assert r['sequestration_rate_derived_by_platform'] is False
    assert r['restoration_success_verified'] is False
    assert r['carbon_credit_eligibility_inferred'] is False


def test_sea_level_scenario_preview_is_screening_only():
    p = scenario_preview({'scenario_height':3,'unit':'ft','bbox':[-90,29,-89,30]})
    r = p['preview']
    assert r['screening_scenario'] is True
    assert r['exact_flood_boundary'] is False
    assert r['parcel_level_forecast'] is False
    assert r['navigation_or_permitting_use'] is False
    assert r['automatic_safety_or_evacuation_action'] is False


def test_bad_source_host_and_cross_source_indicator_are_rejected():
    bad = CLIENT.post('/public/coastal-change/habitat/normalize', json={
        'source_id':'global-mangrove-watch','source_url':'https://example.com/',
        'indicator_type':'mangrove-extent','evidence_class':'habitat-layer','bbox':[1,1,2,2]
    })
    assert bad.status_code == 400
    wrong = CLIENT.get('/public/coastal-change/state?source=noaa-coops&indicator_type=mangrove-extent').json()
    assert wrong['source_supports_indicator_type'] is False


def test_manifest_and_readiness_preserve_architecture_and_truth_boundaries():
    p = export_manifest('noaa-coops','observed-water-level',40.7,-74.0,'2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-coastal-change/1.0'
    assert p['review']['scenario_as_exact_flood_boundary'] is False
    assert p['review']['habitat_as_carbon_stock'] is False
    assert p['review']['habitat_as_carbon_credit'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
    assert r['summary']['primary_area_count_delta'] == 0
