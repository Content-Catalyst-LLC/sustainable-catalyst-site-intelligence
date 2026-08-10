from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.solar_system_navigation_v4400 import catalog, normalize_ephemeris, readiness, state

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_overview_preserves_v4_route_architecture_and_truth_boundary():
    p = CLIENT.get('/public/solar-system-navigation').json()
    assert p['ok'] and p['version'] == '4.26.0' and p['route'] == 'earth'
    assert p['contract'] == 'solar-system-navigation-mission-ephemeris'
    assert p['body_count'] >= 10 and p['mission_context_count'] >= 6
    assert len(p['contract_sha256']) == 64
    assert any('No current body position' in x for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_solar_system_destinations_missions_and_authorities():
    p = catalog()
    ids = {x['id'] for x in p['bodies']}
    assert {'sun', 'earth', 'moon', 'mars', 'jupiter', 'saturn', 'neptune', 'pluto'}.issubset(ids)
    mission_ids = {x['id'] for x in p['missions']}
    assert {'voyager-1', 'juno', 'mars-reconnaissance-orbiter', 'lunar-reconnaissance-orbiter'}.issubset(mission_ids)
    service_ids = {x['id'] for x in p['services']}
    assert {'jpl-horizons', 'naif-spice', 'nasa-eyes'} == service_ids
    assert all(x['orientation_only'] is True for x in p['bodies'])
    assert all(x['current_position_embedded'] is False and x['trajectory_embedded'] is False for x in p['missions'])


def test_state_preserves_navigation_intent_without_inventing_ephemeris():
    p = state('jupiter', 'juno', '2026-08-09T06:32:00Z', 'ECLIPJ2000', 'earth-center')
    assert p['body']['id'] == 'jupiter' and p['mission']['id'] == 'juno'
    assert p['time']['epoch_utc'] == '2026-08-09T06:32:00Z'
    assert p['view']['frame'] == 'ECLIPJ2000' and p['view']['observer']['id'] == 'earth-center'
    e = p['ephemeris']
    assert e['authoritative_solution_loaded'] is False
    assert e['position_vector'] is None and e['velocity_vector'] is None and e['trajectory_points'] == []
    assert e['current_position_claimed'] is False and e['live_trajectory_claimed'] is False
    assert p['truth']['local_orbit_layout_is_ephemeris'] is False
    assert p['truth']['spacecraft_position_fabricated'] is False and p['truth']['trajectory_fabricated'] is False
    assert len(p['state_sha256']) == 64


def test_naive_epoch_is_explicitly_interpreted_as_utc_request_state():
    p = state('mars', '', '2026-08-09T06:32', 'J2000', 'solar-system-barycenter')
    assert p['time']['epoch_utc'] == '2026-08-09T06:32:00Z'
    assert p['time']['assumed_utc'] is True
    assert p['ephemeris']['query_plan']['numerical_result_loaded'] is False


def test_source_attributed_jpl_record_can_be_normalized_without_claiming_network_verification():
    p = normalize_ephemeris({
        'source_kind': 'jpl-horizons',
        'source_url': 'https://ssd.jpl.nasa.gov/horizons/app.html',
        'target_id': 'jupiter',
        'epoch': '2026-08-09T06:32:00Z',
        'frame': 'J2000',
        'observer': 'solar-system-barycenter',
        'position': [1.0, 2.0, 3.0],
        'position_unit': 'au',
        'velocity': [0.01, 0.02, 0.03],
        'velocity_unit': 'au/day',
        'source_record_id': 'fixture-record',
    })
    r = p['ephemeris_record']
    assert r['source_domain_recognized'] is True
    assert r['network_response_independently_verified'] is False
    assert r['evidence_state'] == 'source-attributed-not-network-verified'
    assert r['target']['id'] == 'jupiter' and r['position'] == [1.0, 2.0, 3.0]
    assert len(p['record_sha256']) == 64


def test_unregistered_ephemeris_source_is_rejected_by_public_api():
    response = CLIENT.post('/public/solar-system-navigation/ephemeris/normalize', json={
        'source_kind': 'jpl-horizons',
        'source_url': 'https://example.com/fake',
        'target_id': 'earth',
        'epoch': '2026-08-09T06:32:00Z',
        'position': [1, 2, 3],
    })
    assert response.status_code == 400
    assert 'registered authoritative source host' in response.json()['detail']


def test_export_and_readiness_disclose_non_fabrication_contract():
    p = CLIENT.get('/public/solar-system-navigation/export-manifest', params={
        'body': 'saturn', 'mission': '', 'epoch': '2026-08-09T06:32:00Z', 'frame': 'J2000'
    }).json()
    assert p['schema'] == 'sc-site-intelligence-solar-system-navigation/1.0'
    assert p['review']['ephemeris_fabricated'] is False
    assert p['review']['trajectory_fabricated'] is False
    assert p['review']['live_spacecraft_position_claimed'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and r['checks']['no_fake_ephemeris'] and r['checks']['no_fake_trajectory']
    assert r['summary']['bodies'] >= 10 and r['summary']['missions'] >= 6


def test_solar_system_assets_ship_in_app_service_worker_and_wordpress():
    html = (ROOT / 'backend/public_app/index.html').read_text()
    sw = (ROOT / 'backend/public_app/service-worker.js').read_text()
    js = (ROOT / 'backend/public_app/assets/solar-system-navigation-v4400.js').read_text()
    css = (ROOT / 'backend/public_app/assets/solar-system-navigation-v4400.css').read_text()
    assert 'data-scsi-solar-system-contract="solar-system-navigation-v4400"' in html
    assert 'id="earthSolarSystemEnter"' in html and 'id="solarSystemPanel"' in html
    assert 'solar-system-navigation-v4400.js' in sw and 'solar-system-navigation-v4400.css' in sw
    assert 'SCSISolarSystemV4400' in js and 'NOT EPHEMERIS' in js and '.solar4400-stage' in css
    assert js == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/solar-system-navigation-v4400.js').read_text()
    assert css == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/solar-system-navigation-v4400.css').read_text()
