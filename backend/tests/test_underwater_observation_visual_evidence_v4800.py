from fastapi.testclient import TestClient

from app.main import app
from app.underwater_observation_v4800 import (
    catalog,
    export_manifest,
    normalize_annotation,
    normalize_media,
    readiness,
    state,
)

CLIENT = TestClient(app)


def test_overview_preserves_v4_architecture_and_truth_boundaries():
    p = CLIENT.get('/public/underwater-observation').json()
    assert p['ok'] and p['version'] == '4.37.0' and p['route'] == 'earth'
    assert p['contract'] == 'underwater-observation-visual-evidence'
    assert p['source_count'] == 3 and p['media_type_count'] == 4
    assert any('orientation view' in x.lower() for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_onc_fathomnet_and_noaa_with_rights_boundaries():
    p = catalog()
    ids = {x['id'] for x in p['sources']}
    assert ids == {'onc-oceans-3', 'fathomnet', 'noaa-ocean-exploration'}
    onc = next(x for x in p['sources'] if x['id'] == 'onc-oceans-3')
    fathom = next(x for x in p['sources'] if x['id'] == 'fathomnet')
    noaa = next(x for x in p['sources'] if x['id'] == 'noaa-ocean-exploration')
    assert 'asset-specific' in onc['rights'].lower()
    assert 'blanket reuse license' in fathom['rights'].lower()
    assert 'video portal video is public domain' in noaa['rights'].lower()
    assert len(p['media_types']) == 4


def test_state_never_fabricates_media_or_point_coverage():
    p = state('onc-oceans-3', 'still-image', 48.65, -126.85, '2026-08-09', 870, 'Barkley Canyon')
    assert not p['media']['record_loaded']
    assert p['media']['media_url'] is None
    assert not p['media']['location_verified'] and not p['media']['depth_verified']
    assert not p['truth']['visual_media_fabricated']
    assert not p['truth']['catalog_entry_as_point_coverage']
    assert not p['environmental_context']['co_temporal_verified']
    assert len(p['state_sha256']) == 64


def test_normalize_onc_media_preserves_depth_time_station_rights_and_no_sensor_sync():
    p = normalize_media({
        'source_id': 'onc-oceans-3',
        'source_url': 'https://data.oceannetworks.ca/SeaTube',
        'media_type': 'video-segment',
        'media_url': 'https://data.oceannetworks.ca/SeaTube',
        'source_record_id': 'onc-video-001',
        'station_id': 'BACAX',
        'latitude': 48.65,
        'longitude': -126.85,
        'depth_m': 870,
        'observed_at': '2026-08-01T12:00:00Z',
        'credit': 'Ocean Networks Canada',
        'rights_statement': 'Source-specific use and attribution terms apply.',
        'rights_verified': True,
    })
    m = p['media']
    assert m['depth_m'] == 870.0 and m['station_id'] == 'BACAX'
    assert m['observed_at'] == '2026-08-01T12:00:00Z'
    assert m['rights_verified'] is True and m['credit'] == 'Ocean Networks Canada'
    assert not m['environmental_context_synchronized']
    assert not m['network_response_independently_verified']
    assert len(p['media_sha256']) == 64


def test_fathomnet_model_annotation_remains_model_inference_not_verified_biology():
    media = normalize_media({
        'source_id': 'fathomnet',
        'source_url': 'https://database.fathomnet.org/',
        'media_type': 'still-image',
        'media_url': 'https://database.fathomnet.org/',
        'source_record_id': 'img-123',
        'depth_m': 1200,
    })
    assert media['media']['media_type']['id'] == 'still-image'
    ann = normalize_annotation({
        'source_id': 'fathomnet',
        'source_url': 'https://database.fathomnet.org/',
        'annotation_id': 'ann-1',
        'media_record_id': 'img-123',
        'annotation_type': 'model-inference',
        'label': 'Octopus',
        'concept_id': 'concept-1',
        'bounding_box': [10, 20, 100, 80],
        'confidence': 0.91,
        'source_verified_taxonomy': True,
    })
    a = ann['annotation']
    assert a['bounding_box'] == [10.0, 20.0, 100.0, 80.0]
    assert a['confidence'] == 0.91
    assert a['source_verified_taxonomy'] is True
    assert a['verified_taxonomic_observation'] is False
    assert not a['abundance_claimed'] and not a['population_claimed']


def test_noaa_video_rights_statement_is_preserved_not_generalized():
    p = normalize_media({
        'source_id': 'noaa-ocean-exploration',
        'source_url': 'https://oceanexplorer.noaa.gov/data/access/',
        'media_type': 'video-segment',
        'media_url': 'https://oceanexplorer.noaa.gov/video_playlist.html',
        'source_record_id': 'dive-EXAMPLE-segment-1',
        'dive_id': 'EXAMPLE-DIVE',
        'expedition_id': 'EXAMPLE-EXPEDITION',
        'rights_statement': 'NOAA Ocean Exploration Video Portal video: public domain; attribution requested.',
        'rights_verified': True,
    })
    m = p['media']
    assert m['rights_verified'] is True
    assert 'Video Portal video' in m['rights_statement']
    assert p['review']['rights_inferred'] is False


def test_unregistered_hosts_media_types_and_bad_annotations_are_rejected():
    bad_media = {
        'source_id': 'fathomnet',
        'source_url': 'https://example.com/image',
        'media_type': 'still-image',
        'source_record_id': 'x',
    }
    assert CLIENT.post('/public/underwater-observation/media/normalize', json=bad_media).status_code == 400
    assert CLIENT.get('/public/underwater-observation/state', params={'media_type': 'imaginary-media'}).status_code == 400
    bad_ann = {
        'source_id': 'fathomnet',
        'source_url': 'https://database.fathomnet.org/',
        'annotation_id': 'a',
        'media_record_id': 'm',
        'annotation_type': 'model-inference',
        'label': 'fish',
        'bounding_box': [1, 2, -3, 4],
    }
    assert CLIENT.post('/public/underwater-observation/annotation/normalize', json=bad_ann).status_code == 400


def test_manifest_and_readiness_preserve_review_boundaries_and_route_count():
    p = export_manifest('fathomnet', 'still-image', 36.7, -122, '2026-08-09', 1200, 'Octopus')
    assert p['schema'] == 'sc-site-intelligence-underwater-observation/1.0'
    assert p['review']['visual_media_fabricated'] is False
    assert p['review']['model_as_verified_observation'] is False
    assert p['review']['rights_inferred'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
