from fastapi.testclient import TestClient

from app.main import app
from app.marine_human_activity_v41200 import (
    catalog,
    export_manifest,
    normalize_activity,
    normalize_protected_area,
    overlap_preview,
    readiness,
)

CLIENT = TestClient(app)


def test_overview_preserves_v4_architecture_and_no_compliance_claims():
    p = CLIENT.get('/public/marine-human-activity').json()
    assert p['ok'] and p['version'] == '4.24.0' and p['route'] == 'earth'
    assert p['contract'] == 'marine-human-activity-protected-areas-maritime-pressure'
    assert p['source_count'] == 4 and p['activity_type_count'] >= 8
    assert any('AIS presence' in x for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_open_ocean_planning_activity_sources():
    p = catalog()
    assert {x['id'] for x in p['sources']} == {
        'noaa-marine-cadastre-ais','noaa-mpa-inventory','emodnet-human-activities','global-fishing-watch'
    }
    activities = {x['id'] for x in p['activity_types']}
    assert {'vessel-traffic','fishing-activity','protected-area','offshore-energy','aquaculture'} <= activities


def test_state_starts_without_activity_overlap_or_enforcement_claims():
    p = CLIENT.get('/public/marine-human-activity/state?source=global-fishing-watch&activity_type=fishing-activity&latitude=41.1&longitude=-69.2&date=2026-08-09').json()
    assert p['source_supports_activity_type'] is True
    assert p['evidence']['activity_record_loaded'] is False
    assert p['evidence']['spatial_overlap_evaluated'] is False
    assert p['truth']['zero_ais_treated_as_no_vessel'] is False
    assert p['truth']['fishing_activity_treated_as_illegal'] is False
    assert p['truth']['spatial_overlap_treated_as_violation'] is False
    assert p['truth']['platform_compliance_finding'] is False


def test_activity_normalization_keeps_inference_distinct_from_illegality():
    p = normalize_activity({
        'source_id':'global-fishing-watch',
        'source_url':'https://globalfishingwatch.org/our-apis/',
        'activity_type':'fishing-activity',
        'evidence_class':'inferred-fishing-activity',
        'record_id':'gfw-example',
        'bbox':[-70.0,40.0,-69.0,41.0],
        'observed_at':'2026-08-09T12:00:00Z',
        'value':5.5,
        'unit':'hours',
        'source_classification':'model-inferred fishing activity',
    })
    a=p['activity']
    assert a['inferred_activity'] is True
    assert a['illegal_activity_claimed'] is False
    assert a['complete_vessel_census_claimed'] is False
    assert a['compliance_finding'] is False
    assert p['review']['inferred_fishing_as_illegal'] is False
    assert len(p['activity_sha256']) == 64


def test_protected_area_normalization_does_not_reinterpret_law_or_navigation():
    p = normalize_protected_area({
        'source_id':'noaa-mpa-inventory',
        'source_url':'https://marineprotectedareas.noaa.gov/dataanalysis/mpainventory/',
        'area_id':'example-mpa',
        'name':'Example Marine Protected Area',
        'bbox':[-71.0,39.0,-68.0,42.0],
        'designation':'source-reported designation',
        'protection_level':'source-reported protection class',
        'restriction_text':'source text retained verbatim by caller',
    })
    z=p['protected_area']
    assert z['legal_interpretation_by_platform'] is False
    assert z['navigational_instruction_by_platform'] is False
    assert z['enforcement_status_inferred'] is False
    assert len(p['protected_area_sha256']) == 64


def test_overlap_preview_can_be_true_without_becoming_violation():
    p = overlap_preview({
        'activity_latitude':40.5,
        'activity_longitude':-69.5,
        'zone_bbox':[-70.0,40.0,-69.0,41.0],
        'activity_time':'2026-08-09T12:00:00Z',
        'zone_effective_start':'2026-01-01',
    })
    assert p['preview']['spatial_overlap'] is True
    assert p['preview']['legal_violation'] is False
    assert p['preview']['enforcement_finding'] is False
    assert p['preview']['automatic_action_authorized'] is False
    assert p['preview']['temporal_alignment_verified'] is False
    assert p['review']['spatial_overlap_is_legal_violation'] is False


def test_bad_source_host_and_cross_source_activity_are_rejected():
    wrong = CLIENT.post('/public/marine-human-activity/activity/normalize', json={
        'source_id':'noaa-mpa-inventory','source_url':'https://marineprotectedareas.noaa.gov/dataanalysis/mpainventory/',
        'activity_type':'fishing-activity','evidence_class':'management-attribute',
        'bbox':[-70,40,-69,41],'observed_at':'2026-08-09T00:00:00Z'})
    assert wrong.status_code == 400
    bad = CLIENT.post('/public/marine-human-activity/activity/normalize', json={
        'source_id':'global-fishing-watch','source_url':'https://example.com/',
        'activity_type':'fishing-activity','evidence_class':'inferred-fishing-activity',
        'bbox':[-70,40,-69,41],'observed_at':'2026-08-09T00:00:00Z'})
    assert bad.status_code == 400


def test_manifest_and_readiness_preserve_non_inference_and_route_count():
    p = export_manifest('emodnet-human-activities','offshore-energy',54.0,5.0,'2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-marine-human-activity/1.0'
    assert p['review']['zero_ais_as_no_vessel'] is False
    assert p['review']['fishing_activity_as_illegal'] is False
    assert p['review']['spatial_overlap_as_violation'] is False
    assert p['review']['platform_compliance_finding'] is False
    assert len(p['manifest_sha256']) == 64
    r=readiness(); assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
