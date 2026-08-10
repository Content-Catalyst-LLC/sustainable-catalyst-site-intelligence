from fastapi.testclient import TestClient

from app.main import app
from app.ocean_events_v41100 import catalog, export_manifest, normalize_condition, normalize_event, readiness, threshold_preview

CLIENT = TestClient(app)


def test_overview_preserves_v4_architecture_and_no_automatic_hazard_claims():
    p = CLIENT.get('/public/ocean-events').json()
    assert p['ok'] and p['version'] == '4.25.0' and p['route'] == 'earth'
    assert p['contract'] == 'ocean-events-hazards-ecosystem-change'
    assert p['source_count'] == 4 and p['hazard_type_count'] >= 8
    assert any('threshold crossing' in x.lower() for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_four_sources_and_hazard_domains():
    p = catalog()
    assert {x['id'] for x in p['sources']} == {'noaa-coral-reef-watch','noaa-coastwatch','copernicus-marine','noaa-nccos'}
    hazards = {x['id'] for x in p['hazard_types']}
    assert {'marine-heatwave','coral-heat-stress','harmful-algal-bloom','hypoxia','sea-ice-anomaly','extreme-waves','storm-ocean-impact','ecosystem-change'} <= hazards


def test_state_starts_without_loaded_event_or_warning_claims():
    p = CLIENT.get('/public/ocean-events/state?source=noaa-coral-reef-watch&hazard_type=coral-heat-stress&latitude=18.2&longitude=-66.4&date=2026-08-09').json()
    assert p['source_supports_hazard_type'] is True
    assert p['evidence']['condition_record_loaded'] is False
    assert p['evidence']['source_event_loaded'] is False
    assert p['truth']['hazard_declared'] is False
    assert p['truth']['warning_issued_by_platform'] is False
    assert p['truth']['forecast_treated_as_observation'] is False
    assert p['truth']['zero_records_treated_as_safe'] is False


def test_condition_normalization_preserves_evidence_class_and_does_not_declare_impact():
    p = normalize_condition({
        'source_id':'noaa-coral-reef-watch',
        'source_url':'https://coralreefwatch.noaa.gov/product/5km/',
        'hazard_type':'coral-heat-stress',
        'evidence_class':'satellite-derived',
        'record_id':'crw-example',
        'variable':'Degree Heating Week',
        'value':8.0,
        'unit':'degree C-weeks',
        'latitude':18.2,'longitude':-66.4,
        'observed_at':'2026-08-09T12:00:00Z',
        'source_classification':'source-reported heat-stress class',
    })
    c=p['condition']
    assert c['value']==8.0 and c['evidence_class']=='satellite-derived'
    assert c['hazard_declared_by_platform'] is False
    assert c['warning_issued_by_platform'] is False
    assert c['impact_claimed'] is False
    assert p['review']['metric_recast_as_hazard'] is False
    assert len(p['condition_sha256']) == 64


def test_threshold_preview_can_be_met_without_becoming_warning_or_action():
    p = threshold_preview({'metric':'sst anomaly','value':2.1,'threshold':1.0,'operator':'gte','unit':'degC'})
    assert p['preview']['threshold_met'] is True
    assert p['preview']['hazard_declared'] is False
    assert p['preview']['warning_issued'] is False
    assert p['preview']['automatic_action_authorized'] is False
    assert p['review']['threshold_crossing_is_hazard_declaration'] is False


def test_source_event_stays_source_attributed_and_not_reissued():
    p = normalize_event({
        'source_id':'noaa-coral-reef-watch',
        'source_url':'https://coralreefwatch.noaa.gov/product/5km/',
        'event_id':'example-alert-area',
        'hazard_type':'coral-heat-stress',
        'source_classification':'Bleaching Alert Area source classification',
        'issued_at':'2026-08-09T12:00:00Z',
        'latitude':18.2,'longitude':-66.4,
    })
    assert p['event']['source_reported_event'] is True
    assert p['event']['platform_reissued_warning'] is False
    assert p['event']['platform_upgraded_severity'] is False
    assert p['event']['automatic_action_authorized'] is False


def test_cross_source_hazard_and_bad_host_are_rejected():
    wrong = CLIENT.post('/public/ocean-events/condition/normalize', json={
        'source_id':'noaa-coral-reef-watch','source_url':'https://coralreefwatch.noaa.gov/product/5km/',
        'hazard_type':'harmful-algal-bloom','evidence_class':'satellite-derived',
        'variable':'x','value':1,'unit':'1','observed_at':'2026-08-09T00:00:00Z'})
    assert wrong.status_code == 400
    bad = CLIENT.post('/public/ocean-events/event/normalize', json={
        'source_id':'noaa-coral-reef-watch','source_url':'https://example.com/',
        'hazard_type':'coral-heat-stress','event_id':'x','source_classification':'x'})
    assert bad.status_code == 400


def test_manifest_and_readiness_preserve_non_inference_and_route_count():
    p = export_manifest('copernicus-marine','marine-heatwave',35.0,-145.0,'2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-ocean-events-hazards/1.0'
    assert p['review']['threshold_as_hazard_declaration'] is False
    assert p['review']['forecast_as_observation'] is False
    assert p['review']['source_advisory_reissued'] is False
    assert p['review']['zero_records_as_safe'] is False
    assert len(p['manifest_sha256']) == 64
    r=readiness(); assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
