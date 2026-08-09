from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.record_provenance_v3238 import RecordProvenanceCenter, MAP_LAYERS

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def test_indicator_truth_discloses_snapshot_units_dates_and_fingerprint():
    payload = CLIENT.get('/public/record-truth/indicator/KEN/SP.POP.TOTL').json()
    assert payload['ok'] is True
    assert payload['version'] == '4.5.0'
    assert payload['record_id'] == 'indicator:KEN:SP.POP.TOTL'
    assert payload['record_type'] == 'indicator'
    assert payload['truth_state'] == 'historical_snapshot'
    assert payload['value']['available'] is True
    assert payload['units']['original'] == 'people'
    assert payload['units']['conversion_applied'] is False
    assert payload['dates']['observation_year'] == 2023
    assert payload['source']['publisher'] == 'World Bank Open Data'
    assert payload['source']['url'].startswith('https://')
    assert len(payload['fingerprint']['value']) == 64
    assert len(payload['transformations']) == 4


def test_missing_indicator_remains_missing_without_imputation():
    payload = CLIENT.get('/public/record-truth/indicator/BRA/SP.POP.TOTL').json()
    assert payload['truth_state'] == 'missing'
    assert payload['value']['available'] is False
    assert payload['value']['number'] is None
    assert payload['dates']['observation_at'] is None
    assert any('not imputed' in item.lower() or 'missing' in item.lower() for item in payload['limitations'])


def test_indicator_fingerprint_is_deterministic_for_same_record_contract():
    settings = Settings()
    center = RecordProvenanceCenter(settings)
    first = center.indicator('GHA', 'population')
    second = center.indicator('GHA', 'SP.POP.TOTL')
    assert first['record_id'] == second['record_id']
    assert first['fingerprint']['value'] == second['fingerprint']['value']


def test_country_record_catalog_has_all_indicators_and_export_link():
    payload = CLIENT.get('/public/record-truth/country/KEN').json()
    assert payload['contract'] == 'country-record-provenance-catalog'
    assert payload['country']['code'] == 'KEN'
    assert payload['record_count'] == 8
    assert len(payload['records']) == 8
    assert payload['summary']['historical_snapshot'] == 8
    assert payload['export_endpoint'].endswith('country=KEN')


def test_map_layer_truth_is_context_only_and_no_pixel_inference():
    layer_id = 'true-color'
    assert layer_id in MAP_LAYERS
    payload = CLIENT.get(f'/public/record-truth/map-layer/{layer_id}?date=2026-08-05').json()
    assert payload['record_type'] == 'map_layer'
    assert payload['truth_state'] == 'context_only'
    assert payload['dates']['observation_at'] == '2026-08-05'
    assert payload['source']['publisher'].startswith('NASA')
    assert any(step['operation'] == 'no-pixel-inference' for step in payload['transformations'])


def test_unknown_country_indicator_and_layer_return_404():
    assert CLIENT.get('/public/record-truth/indicator/ZZZ/SP.POP.TOTL').status_code == 404
    assert CLIENT.get('/public/record-truth/indicator/KEN/NOT.A.REAL.INDICATOR').status_code == 404
    assert CLIENT.get('/public/record-truth/map-layer/not-a-layer').status_code == 404


def test_normalized_event_record_preserves_source_and_discloses_unverified_boundary():
    response = CLIENT.post('/public/record-truth/resolve', json={
        'record_type': 'event',
        'id': 'usgs-example',
        'title': 'Example earthquake record',
        'source': 'USGS',
        'source_url': 'https://earthquake.usgs.gov/example',
        'observed_at': '2026-08-05T12:00:00Z',
        'country_code': 'USA',
        'data_state': 'live',
        'summary': 'Public source record.',
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['record_type'] == 'event'
    assert payload['truth_state'] == 'observed'
    assert payload['record_id'] == 'event:usgs-example'
    assert payload['source']['url'].startswith('https://')
    assert any('does not independently' in item for item in payload['limitations'])


def test_normalizer_rejects_non_http_source_url_without_fabricating_one():
    payload = CLIENT.post('/public/record-truth/resolve', json={
        'record_type': 'table-record',
        'id': 'unsafe-url',
        'title': 'Unsafe URL test',
        'source_url': 'javascript:alert(1)',
        'data_state': 'live',
    }).json()
    assert payload['source']['url'] is None
    assert payload['truth_state'] == 'unverified'


def test_manifest_exports_indicator_and_map_layer_fingerprints():
    payload = CLIENT.get('/public/record-truth/manifest?country=KEN').json()
    assert payload['contract'] == 'record-provenance-export-manifest'
    assert payload['country']['code'] == 'KEN'
    assert payload['entry_count'] == 8 + len(MAP_LAYERS)
    assert len(payload['manifest_fingerprint']) == 64
    assert all(len(entry['fingerprint']) == 64 for entry in payload['entries'])
    assert {entry['record_type'] for entry in payload['entries']} == {'indicator', 'map_layer'}


def test_browser_assets_expose_record_truth_controls_and_wordpress_parity():
    html = (ROOT / 'backend/public_app/index.html').read_text()
    app_js = (ROOT / 'backend/public_app/assets/app.js').read_text()
    truth_js = (ROOT / 'backend/public_app/assets/data-truth-v32371.js').read_text()
    record_js = (ROOT / 'backend/public_app/assets/record-provenance-v3238.js').read_text()
    worker = (ROOT / 'backend/public_app/service-worker.js').read_text()
    assert 'record-provenance-v3238.css?v=4.5.0' in html
    assert 'record-provenance-v3238.js?v=4.5.0' in html
    assert 'data-record-truth-layer="true-color"' in html
    assert 'data-record-truth-indicator' in truth_js
    assert 'eventRecordTruthButton' in app_js
    assert 'SCSIRecordProvenanceV3238' in record_js
    assert '/public/record-truth/resolve' in record_js
    assert 'record-provenance-v3238.js' in worker
    assert (ROOT / 'backend/public_app/assets/record-provenance-v3238.js').read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/record-provenance-v3238.js').read_bytes()
    assert (ROOT / 'backend/public_app/assets/record-provenance-v3238.css').read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/record-provenance-v3238.css').read_bytes()
