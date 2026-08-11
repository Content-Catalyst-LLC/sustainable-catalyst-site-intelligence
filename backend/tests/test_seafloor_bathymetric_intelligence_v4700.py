from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.seafloor_bathymetry_v4700 import catalog, normalize_sample, normalize_footprint, readiness, state

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_overview_preserves_v4_architecture_and_truth_boundaries():
    p = CLIENT.get('/public/seafloor-intelligence').json()
    assert p['ok'] and p['version'] == '4.35.11' and p['route'] == 'earth'
    assert p['source_count'] == 3 and p['layer_count'] >= 8
    assert any('Grid spacing' in x for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_gebco_emodnet_and_noaa():
    p = catalog()
    ids = {x['id'] for x in p['sources']}
    assert ids == {'gebco-2026', 'emodnet-bathymetry', 'noaa-ncei-bathymetry'}
    gebco = next(x for x in p['sources'] if x['id'] == 'gebco-2026')
    assert '15 arc-second' in gebco['resolution']
    noaa = next(x for x in p['sources'] if x['id'] == 'noaa-ncei-bathymetry')
    assert 'multibeam' in noaa['coverage']


def test_state_does_not_fabricate_seafloor_depth_or_coverage():
    p = state('bathymetric-elevation', 'gebco-2026', 0, -30, '2026-08-09')
    assert p['terrain']['value'] is None
    assert not p['terrain']['record_loaded'] and not p['terrain']['point_coverage_verified']
    assert not p['truth']['terrain_fabricated'] and not p['truth']['grid_spacing_as_accuracy']
    assert p['query_plan']['grid_release'] == 'GEBCO_2026'
    assert len(p['state_sha256']) == 64


def test_invalid_source_layer_pair_rejected():
    r = CLIENT.get('/public/seafloor-intelligence/state', params={'layer':'singlebeam-tracklines','source':'gebco-2026'})
    assert r.status_code == 400
    r = CLIENT.get('/public/seafloor-intelligence/state', params={'latitude':91})
    assert r.status_code == 400


def test_normalize_source_attributed_grid_sample_preserves_datum_and_resolution():
    p = normalize_sample({
        'layer_id':'bathymetric-elevation','source_id':'gebco-2026','source_url':'https://download.gebco.net/',
        'evidence_type':'global-gridded-bathymetry','source_record_id':'grid-cell-1','latitude':0,'longitude':-30,
        'value':-4217,'unit':'m','vertical_datum':'source-defined elevation reference','source_resolution':'15 arc-second','source_type':'grid-cell'
    })
    s = p['sample']
    assert s['value'] == -4217.0 and s['vertical_datum'] == 'source-defined elevation reference'
    assert s['source_resolution'] == '15 arc-second'
    assert not s['sign_or_datum_conversion_performed'] and not s['network_response_independently_verified']
    assert len(p['sample_sha256']) == 64


def test_normalize_survey_footprint_never_turns_extent_into_point_measurement():
    p = normalize_footprint({
        'source_id':'noaa-ncei-bathymetry','source_url':'https://www.ncei.noaa.gov/products/bathymetry',
        'footprint_id':'survey-123','dataset_id':'dataset-123','survey_type':'multibeam',
        'geometry':{'type':'Polygon','coordinates':[[[-70,40],[-69,40],[-69,41],[-70,41],[-70,40]]]}
    })
    f = p['footprint']
    assert not f['point_measurement_claimed'] and not f['uniform_density_claimed'] and not f['quality_claimed']
    assert len(p['footprint_sha256']) == 64


def test_unregistered_hosts_and_bad_geometry_rejected():
    base={'layer_id':'bathymetric-elevation','source_id':'gebco-2026','source_url':'https://example.com/a','evidence_type':'global-gridded-bathymetry','source_record_id':'x','latitude':0,'longitude':0,'value':-100}
    assert CLIENT.post('/public/seafloor-intelligence/sample/normalize',json=base).status_code == 400
    bad={'source_id':'noaa-ncei-bathymetry','source_url':'https://www.ncei.noaa.gov/products/bathymetry','footprint_id':'x','geometry':{'type':'Point','coordinates':[0,0]}}
    assert CLIENT.post('/public/seafloor-intelligence/footprint/normalize',json=bad).status_code == 400


def test_export_manifest_and_readiness():
    m = CLIENT.get('/public/seafloor-intelligence/export-manifest', params={'latitude':-20,'longitude':-110}).json()
    assert m['schema'] == 'sc-site-intelligence-seafloor-bathymetry/1.0'
    assert len(m['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values()) and r['summary']['public_route_count_delta'] == 0
