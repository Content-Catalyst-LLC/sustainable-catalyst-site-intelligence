from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.water_column_v4600 import catalog, normalize_profile, readiness, resolve_depth, state

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_overview_preserves_v4_architecture_and_truth_boundaries():
    p = CLIENT.get('/public/water-column').json()
    assert p['ok'] and p['version'] == '4.18.0' and p['route'] == 'earth'
    assert p['source_count'] >= 3 and p['variable_count'] >= 8 and p['maximum_navigation_depth_m'] == 11000.0
    assert any('does not interpolate' in x for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_argo_copernicus_and_onc():
    p = catalog()
    ids = {x['id'] for x in p['sources']}
    assert ids == {'argo-argovis', 'copernicus-marine', 'onc-oceans-3'}
    assert 'Argovis REST API' in next(x for x in p['sources'] if x['id'] == 'argo-argovis')['machine_access']
    assert 'not global' in next(x for x in p['sources'] if x['id'] == 'onc-oceans-3')['coverage']
    assert p['depth_presets_m'][-1] == 11000


def test_state_does_not_fabricate_depth_sample():
    p = state('temperature', 'argo-argovis', 22.5, -158.0, '2026-08-09', 1000)
    assert p['condition']['value'] is None
    assert not p['condition']['record_loaded'] and not p['condition']['depth_sample_verified']
    assert p['query_plan']['api_base'] == 'https://argovis-api.colorado.edu/argo'
    assert not p['truth']['depth_value_interpolated'] and not p['truth']['nearest_sample_substituted']
    assert len(p['state_sha256']) == 64


def test_invalid_depth_and_source_variable_pair_rejected():
    assert CLIENT.get('/public/water-column/state', params={'depth_m': -1}).status_code == 400
    assert CLIENT.get('/public/water-column/state', params={'depth_m': 12000}).status_code == 400
    assert CLIENT.get('/public/water-column/state', params={'variable': 'pressure', 'source': 'copernicus-marine'}).status_code == 400


def test_source_attributed_profile_preserves_samples_and_qc():
    p = normalize_profile({
        'variable_id': 'temperature', 'source_id': 'argo-argovis',
        'source_url': 'https://argovis-api.colorado.edu/argo', 'evidence_type': 'in-situ-profile',
        'profile_id': 'fixture-profile', 'platform_id': '5900000', 'latitude': 22.5, 'longitude': -158.0,
        'observed_at': '2026-08-08T12:00:00Z',
        'samples': [
            {'depth_m': 1000, 'pressure_dbar': 1008, 'value': 4.1, 'unit': 'degC', 'quality_flags': ['1']},
            {'depth_m': 0, 'pressure_dbar': 0, 'value': 26.4, 'unit': 'degC', 'quality_flags': ['1']},
            {'depth_m': 500, 'pressure_dbar': 504, 'value': 8.7, 'unit': 'degC', 'quality_flags': ['2']},
        ]})
    profile = p['profile']
    assert [x['depth_m'] for x in profile['samples']] == [0.0, 500.0, 1000.0]
    assert profile['samples'][1]['quality_flags'] == ['2']
    assert not profile['interpolation_performed'] and not profile['network_response_independently_verified']
    assert len(p['profile_sha256']) == 64


def test_depth_resolution_returns_exact_only_and_withholds_nearest():
    samples = [{'depth_m': 0, 'value': 20}, {'depth_m': 100, 'value': 15}, {'depth_m': 200, 'value': 10}]
    exact = resolve_depth({'target_depth_m': 100, 'samples': samples, 'unit': 'degC'})['resolution']
    assert exact['value'] == 15 and exact['value_claimed'] and exact['match'] == 'exact-source-sample'
    missing = resolve_depth({'target_depth_m': 150, 'samples': samples, 'unit': 'degC'})['resolution']
    assert missing['value'] is None and not missing['value_claimed'] and not missing['interpolation_performed']
    assert missing['nearest_available_sample']['depth_m'] in {100.0, 200.0}
    assert missing['nearest_available_sample']['value_withheld_as_target_value']


def test_duplicate_depths_and_unregistered_host_rejected():
    base = {'variable_id':'temperature','source_id':'argo-argovis','source_url':'https://example.com/x','evidence_type':'in-situ-profile','profile_id':'x','latitude':0,'longitude':0,'observed_at':'2026-08-09T00:00:00Z','samples':[{'depth_m':0,'value':20}]}
    assert CLIENT.post('/public/water-column/profile/normalize', json=base).status_code == 400
    base['source_url'] = 'https://argovis-api.colorado.edu/argo'
    base['samples'] = [{'depth_m': 10, 'value': 20}, {'depth_m': 10, 'value': 19}]
    assert CLIENT.post('/public/water-column/profile/normalize', json=base).status_code == 400


def test_export_and_readiness():
    p = CLIENT.get('/public/water-column/export-manifest', params={'variable':'dissolved-oxygen','source':'copernicus-marine','latitude':0,'longitude':-140,'date':'2026-08-09','depth_m':500}).json()
    assert p['schema'] == 'sc-site-intelligence-water-column/1.0'
    assert not p['review']['depth_value_fabricated'] and not p['review']['interpolation_performed'] and not p['review']['nearest_sample_substituted']
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and r['summary']['public_route_count_delta'] == 0


def test_assets_ship_with_ocean_loader_service_worker_and_wordpress():
    ocean_js = (ROOT/'backend/public_app/assets/ocean-surface-v4500.js').read_text()
    sw = (ROOT/'backend/public_app/service-worker.js').read_text()
    js = (ROOT/'backend/public_app/assets/water-column-v4600.js').read_text()
    css = (ROOT/'backend/public_app/assets/water-column-v4600.css').read_text()
    assert 'water-column-v4600.js' in ocean_js
    assert 'water-column-v4600.js' in sw and 'water-column-v4600.css' in sw
    assert 'SCSIWaterColumnV4600' in js and 'NO PROFILE SAMPLE RENDERED' in js and '.water4600-stage' in css
    assert js == (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.js').read_text()
    assert css == (ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/water-column-v4600.css').read_text()
