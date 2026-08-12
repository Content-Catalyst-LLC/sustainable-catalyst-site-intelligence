from fastapi.testclient import TestClient

from app.main import app
from app.ocean_missions_v41000 import (
    catalog,
    export_manifest,
    normalize_mission,
    normalize_platform,
    normalize_track,
    readiness,
    state,
)

CLIENT = TestClient(app)


def test_overview_preserves_v4_architecture_and_no_live_position_claims():
    p = CLIENT.get('/public/ocean-missions').json()
    assert p['ok'] and p['version'] == '4.35.19' and p['route'] == 'earth'
    assert p['contract'] == 'ocean-missions-vehicles-observatory-network'
    assert p['source_count'] == 4 and p['platform_type_count'] >= 10
    assert any('last reported position' in x.lower() for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_networks_and_platform_classes():
    p = catalog()
    assert {x['id'] for x in p['sources']} == {'argo', 'ioos', 'onc', 'noaa-ocean-exploration'}
    types = {x['id'] for x in p['platform_types']}
    for expected in {'float', 'glider', 'buoy', 'auv', 'rov', 'research-vessel', 'fixed-observatory', 'camera-station', 'hydrophone-station'}:
        assert expected in types


def test_state_is_query_context_not_a_loaded_platform_or_live_position():
    p = state('argo', 'float', '5901234', 35.0, -145.0, '2026-08-09')
    assert p['platform_id'] == '5901234'
    assert p['query_point'] == {'latitude': 35.0, 'longitude': -145.0}
    assert p['evidence']['platform_record_loaded'] is False
    assert p['truth']['current_position_verified'] is False
    assert p['truth']['continuous_trajectory_verified'] is False
    assert p['truth']['registry_presence_as_active_operation'] is False
    assert len(p['state_sha256']) == 64


def test_platform_record_preserves_last_reported_position_without_recasting_current():
    p = normalize_platform({
        'source_id': 'argo',
        'source_url': 'https://argovis.colorado.edu/',
        'platform_id': '5901234',
        'platform_type': 'float',
        'name': 'Argo 5901234',
        'source_status': 'operating',
        'status_time': '2026-08-08T12:00:00Z',
        'latitude': 35.1,
        'longitude': -145.2,
        'position_time': '2026-08-08T11:48:00Z',
        'position_kind': 'last-reported',
    })
    record = p['platform']
    assert record['source_reported_position'] is True
    assert record['source_reported_status'] is True
    assert record['current_position_claimed'] is False
    assert record['current_operational_status_claimed'] is False
    assert p['review']['last_reported_position_recast_as_current'] is False
    assert len(p['platform_sha256']) == 64


def test_historical_noaa_mission_is_not_promoted_to_live_operation():
    p = normalize_mission({
        'source_id': 'noaa-ocean-exploration',
        'source_url': 'https://oceanexplorer.noaa.gov/data/access-tools/',
        'mission_id': 'expedition-example',
        'title': 'Archived expedition',
        'platform_ids': ['Okeanos Explorer', 'ROV Deep Discoverer'],
        'source_status': 'completed',
        'start_time': '2025-06-01T00:00:00Z',
        'end_time': '2025-06-20T00:00:00Z',
    })
    assert p['mission']['source_status'] == 'completed'
    assert p['mission']['current_operation_claimed'] is False
    assert p['review']['historical_mission_recast_as_live'] is False
    assert len(p['mission_sha256']) == 64


def test_discrete_track_points_are_not_interpolated_or_extended():
    p = normalize_track({
        'source_id': 'argo',
        'source_url': 'https://argovis.colorado.edu/',
        'platform_id': '5901234',
        'track_id': 'track-1',
        'points': [
            {'latitude': 35.0, 'longitude': -145.0, 'time': '2026-08-01T00:00:00Z'},
            {'latitude': 35.4, 'longitude': -144.6, 'time': '2026-08-04T00:00:00Z'},
        ],
    })
    t = p['track']
    assert t['point_count'] == 2
    assert t['interpolation_applied'] is False
    assert t['continuous_path_claimed'] is False
    assert t['current_position_claimed'] is False
    assert t['future_trajectory_claimed'] is False
    assert p['review']['points_interpolated'] is False


def test_cross_source_platform_types_and_bad_hosts_are_rejected():
    wrong = CLIENT.post('/public/ocean-missions/platform/normalize', json={
        'source_id': 'argo', 'source_url': 'https://argovis.colorado.edu/',
        'platform_id': 'x', 'platform_type': 'rov'
    })
    assert wrong.status_code == 400
    bad = CLIENT.post('/public/ocean-missions/platform/normalize', json={
        'source_id': 'argo', 'source_url': 'https://example.com/',
        'platform_id': 'x', 'platform_type': 'float'
    })
    assert bad.status_code == 400
    incomplete_position = CLIENT.post('/public/ocean-missions/platform/normalize', json={
        'source_id': 'argo', 'source_url': 'https://argovis.colorado.edu/',
        'platform_id': 'x', 'platform_type': 'float', 'latitude': 1, 'longitude': 2
    })
    assert incomplete_position.status_code == 400


def test_track_rejects_incomplete_points():
    bad = CLIENT.post('/public/ocean-missions/track/normalize', json={
        'source_id': 'argo', 'source_url': 'https://argovis.colorado.edu/',
        'platform_id': '5901234', 'track_id': 'bad',
        'points': [{'latitude': 35, 'longitude': -145}]
    })
    assert bad.status_code == 400


def test_manifest_and_readiness_preserve_non_inference_and_route_count():
    p = export_manifest('onc', 'fixed-observatory', 'Barkley-Canyon', 48.3, -126.0, '2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-ocean-missions-network/1.0'
    assert p['review']['registry_presence_as_active'] is False
    assert p['review']['last_reported_position_as_current'] is False
    assert p['review']['discrete_points_as_continuous_trajectory'] is False
    assert p['review']['future_position_predicted'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
