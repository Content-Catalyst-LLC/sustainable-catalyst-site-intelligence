from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.orbital_earth_v4100 import catalog, readiness, state

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_orbital_overview_extends_existing_earth_route_without_new_top_level_route():
    payload = CLIENT.get('/public/orbital-earth').json()
    assert payload['ok'] is True
    assert payload['version'] == '4.35.22'
    assert payload['contract'] == 'orbital-earth-satellite-observation'
    assert payload['route'] == 'earth'
    assert payload['mode'] == 'orbital'
    assert payload['real_satellite_imagery'] is True
    assert payload['presentation'] == '2.5d-orbital-perspective'
    assert len(payload['contract_sha256']) == 64
    navigation = CLIENT.get('/public/v4/navigation').json()
    assert navigation['route_count'] == 35
    assert any(row['route_id'] == 'earth' for row in navigation['routes'])


def test_orbital_catalog_maps_all_registered_layers_to_platform_context_without_ephemeris_claims():
    payload = catalog()
    assert payload['layer_count'] >= 8
    ids = {row['layer_id'] for row in payload['layers']}
    assert {'true-color','land-surface-temperature','fires-thermal-anomalies','vegetation-index','precipitation-rate','snow-cover','nighttime-lights','aerosol-optical-depth'} <= ids
    for row in payload['layers']:
        assert row['platform']
        assert row['instrument']
        assert row['real_time_position_available'] is False
        assert row['instantaneous_sensor_swath_available'] is False
        assert row['coverage_footprint']['kind'] == 'registered-product-coverage-envelope'


def test_orbital_state_uses_registered_real_imagery_and_explicit_truth_boundaries():
    payload = state('true-color','2026-08-01',41.8781,-87.6298,500)
    observation = payload['observation']
    assert payload['version'] == '4.35.22'
    assert observation['requested_date'] == '2026-08-01'
    assert observation['layer_id'] == 'true-color'
    assert 'gibs.earthdata.nasa.gov' in observation['tile_url']
    assert observation['platform'].startswith('Suomi')
    assert observation['instrument'] == 'VIIRS'
    assert payload['orbit_context']['real_time_spacecraft_position'] is None
    assert payload['orbit_context']['ground_track'] is None
    assert payload['orbit_context']['ephemeris_connected'] is False
    assert payload['footprints']['instantaneous_sensor_swath'] is None
    assert len(payload['state_sha256']) == 64


def test_orbital_state_clamps_visual_perspective_and_geography_without_silent_source_substitution():
    payload = state('missing-layer','not-a-date',95,500,999999)
    assert payload['view']['center'] == [85.0,180.0]
    assert payload['view']['presentation_altitude_km'] == 35786.0
    assert payload['view']['altitude_is_physical_camera_solution'] is False
    assert payload['observation']['layer_id'] == 'true-color'
    assert payload['orbit_context']['illustrative_orbit_rings_only'] is True


def test_orbital_export_manifest_is_reproducible_evidence_not_live_telemetry():
    payload = CLIENT.get('/public/orbital-earth/export-manifest',params={'layer':'nighttime-lights','date':'2026-08-01','latitude':0,'longitude':20,'altitude_km':2000}).json()
    assert payload['schema'] == 'sc-site-intelligence-orbital-view/1.0'
    assert payload['review']['real_satellite_imagery'] is True
    assert payload['review']['live_spacecraft_position_claimed'] is False
    assert payload['review']['instantaneous_swath_claimed'] is False
    assert payload['review']['human_interpretation_required'] is True
    assert len(payload['manifest_sha256']) == 64


def test_orbital_readiness_requires_truthful_imagery_contract():
    payload = readiness()
    assert payload['ok'] is True
    assert all(payload['checks'].values())
    assert payload['summary']['route'] == 'earth'
    assert payload['summary']['layers'] >= 8
    assert len(payload['readiness_sha256']) == 64


def test_orbital_browser_assets_are_shipped_in_app_service_worker_and_wordpress_package():
    html=(ROOT/'backend/public_app/index.html').read_text()
    sw=(ROOT/'backend/public_app/service-worker.js').read_text()
    js=(ROOT/'backend/public_app/assets/orbital-earth-v4100.js').read_text()
    css=(ROOT/'backend/public_app/assets/orbital-earth-v4100.css').read_text()
    assert 'data-scsi-orbital-contract="orbital-earth-v4100"' in html
    assert 'orbital-earth-v4100.css?v=4.35.22' in html
    assert 'orbital-earth-v4100.js?v=4.35.22' in html
    assert 'id="earthOrbitPanel"' in html
    assert 'id="earthOrbitMap"' in js
    assert 'orbital-earth-v4100.css' in sw and 'orbital-earth-v4100.js' in sw
    assert 'SCSIOrbitalEarthV4100' in js
    assert '.earth-orbit-stage' in css and '.earth-globe-shell' in css
    assert js == (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.js').read_text()
    assert css == (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/orbital-earth-v4100.css').read_text()


def test_earth_observation_overview_advertises_orbital_extension():
    payload=CLIENT.get('/public/earth-observation').json()
    assert payload['version']=='4.35.22'
    assert payload['orbital_contract']=='/public/orbital-earth'
    assert 'surface-to-orbit transition' in payload['capabilities']
    assert 'orbital Earth perspective' in payload['capabilities']
