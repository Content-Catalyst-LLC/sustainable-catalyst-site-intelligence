from fastapi.testclient import TestClient

from app.main import app
from app.marine_biodiversity_v4900 import (
    catalog,
    export_manifest,
    normalize_acoustic,
    normalize_occurrence,
    normalize_taxonomy,
    normalize_visual,
    readiness,
    state,
)

CLIENT = TestClient(app)


def test_overview_preserves_v4_architecture_and_evidence_boundaries():
    p = CLIENT.get('/public/marine-biodiversity').json()
    assert p['ok'] and p['version'] == '4.21.0' and p['route'] == 'earth'
    assert p['contract'] == 'marine-biodiversity-bioacoustic-intelligence'
    assert p['source_count'] == 4 and p['evidence_class_count'] == 6
    assert any('no returned occurrence records' in x.lower() for x in p['truth_boundaries'])
    nav = CLIENT.get('/public/v4/navigation').json()
    assert nav['route_count'] == 35 and nav['primary_area_count'] == 6


def test_catalog_registers_obis_worms_fathomnet_and_onc_hydrophones():
    p = catalog()
    assert {x['id'] for x in p['sources']} == {'obis', 'worms', 'fathomnet', 'onc-hydrophones'}
    assert len(p['evidence_classes']) == 6
    assert len(p['annotation_methods']) == 4
    assert len(p['acoustic_methods']) == 4


def test_state_loads_no_biodiversity_evidence_and_does_not_infer_absence():
    p = state('obis', 'occurrence-record', 'Octopus', 36.7, -122.0, 1200, '2026-08-09')
    assert p['evidence']['records_loaded'] is False
    assert p['evidence']['record_count'] is None
    assert p['evidence']['presence_verified'] is False
    assert p['evidence']['absence_verified'] is False
    assert p['truth']['zero_results_as_absence'] is False
    assert len(p['state_sha256']) == 64


def test_obis_occurrence_preserves_explicit_absence_without_generalizing_it():
    p = normalize_occurrence({
        'source_id': 'obis',
        'source_url': 'https://api.obis.org/',
        'occurrence_id': 'obis-occ-1',
        'scientific_name': 'Example species',
        'scientific_name_id': 'urn:lsid:marinespecies.org:taxname:123',
        'occurrence_status': 'absent',
        'event_date': '2026-08-01',
        'latitude': 48.5,
        'longitude': -126.2,
        'depth_m': 900,
    })
    o = p['occurrence']
    assert o['explicit_absence'] is True
    assert o['population_size_claimed'] is False
    assert o['continued_presence_claimed'] is False
    assert p['review']['zero_results_recast_as_absence'] is False
    assert len(p['occurrence_sha256']) == 64


def test_worms_taxonomy_is_authority_record_not_occurrence():
    p = normalize_taxonomy({
        'source_id': 'worms',
        'source_url': 'https://www.marinespecies.org/rest/',
        'aphia_id': '127160',
        'scientific_name': 'Solea solea',
        'rank': 'Species',
        'status': 'accepted',
        'classification': ['Animalia', 'Chordata', 'Actinopterygii'],
    })
    t = p['taxonomy']
    assert t['aphia_id'] == '127160'
    assert t['occurrence_claimed'] is False and t['distribution_claimed'] is False
    assert p['review']['taxonomy_promoted_to_occurrence'] is False
    assert len(p['taxonomy_sha256']) == 64


def test_fathomnet_model_visual_label_is_not_verified_species_or_occurrence():
    p = normalize_visual({
        'source_id': 'fathomnet',
        'source_url': 'https://database.fathomnet.org/',
        'annotation_id': 'ann-4900',
        'media_record_id': 'img-4900',
        'label': 'Octopus',
        'annotation_method': 'model-inference',
        'confidence': 0.94,
        'source_verified_taxonomy': True,
    })
    v = p['visual']
    assert v['confidence'] == 0.94
    assert v['verified_taxonomic_observation'] is False
    assert v['occurrence_record_created'] is False
    assert v['abundance_claimed'] is False
    assert p['review']['model_promoted_to_verified_species'] is False


def test_onc_raw_recording_is_not_detection_and_model_detection_not_verified_species():
    raw = normalize_acoustic({
        'source_id': 'onc-hydrophones',
        'source_url': 'https://data.oceannetworks.ca/',
        'record_id': 'hydro-raw-1',
        'method': 'raw-recording',
        'station_id': 'FOLGER-DEEP',
        'hydrophone_id': '1266',
    })['acoustic']
    assert raw['recording_loaded'] is True and raw['detection_claimed'] is False

    model = normalize_acoustic({
        'source_id': 'onc-hydrophones',
        'source_url': 'https://data.oceannetworks.ca/',
        'record_id': 'hydro-model-1',
        'method': 'model-detection',
        'label': 'Orca call',
        'confidence': 0.88,
        'source_verified_taxonomy': True,
        'frequency_min_hz': 500,
        'frequency_max_hz': 12000,
    })
    a = model['acoustic']
    assert a['detection_claimed'] is True
    assert a['verified_detection'] is False
    assert a['verified_species_presence'] is False
    assert a['abundance_claimed'] is False
    assert model['review']['model_detection_promoted_to_verified_species'] is False


def test_bad_hosts_invalid_frequency_and_cross_source_normalizers_are_rejected():
    bad = CLIENT.post('/public/marine-biodiversity/occurrence/normalize', json={
        'source_id': 'obis', 'source_url': 'https://example.com/',
        'occurrence_id': 'x', 'scientific_name': 'fish'
    })
    assert bad.status_code == 400
    bad_freq = CLIENT.post('/public/marine-biodiversity/acoustic/normalize', json={
        'source_id': 'onc-hydrophones', 'source_url': 'https://data.oceannetworks.ca/',
        'record_id': 'x', 'method': 'model-detection', 'label': 'call',
        'frequency_min_hz': 10000, 'frequency_max_hz': 1000
    })
    assert bad_freq.status_code == 400
    wrong_source = CLIENT.post('/public/marine-biodiversity/taxonomy/normalize', json={
        'source_id': 'obis', 'source_url': 'https://api.obis.org/',
        'aphia_id': '1', 'scientific_name': 'x'
    })
    assert wrong_source.status_code == 400


def test_manifest_and_readiness_preserve_non_inference_and_route_count():
    p = export_manifest('onc-hydrophones', 'acoustic-recording', 'Orcinus orca', 48.5, -126.2, 900, '2026-08-09')
    assert p['schema'] == 'sc-site-intelligence-marine-biodiversity-bioacoustic/1.0'
    assert p['review']['zero_results_as_absence'] is False
    assert p['review']['model_detection_as_verified_species'] is False
    assert p['review']['acoustic_detection_as_abundance'] is False
    assert len(p['manifest_sha256']) == 64
    r = readiness()
    assert r['ok'] and all(r['checks'].values())
    assert r['summary']['public_route_count_delta'] == 0
