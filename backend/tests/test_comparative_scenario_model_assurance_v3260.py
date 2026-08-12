from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.comparative_model_assurance_v3260 import ComparativeModelAssuranceCenter

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def test_assurance_schema_discloses_boundaries_and_capabilities():
    payload = CLIENT.get('/public/assurance').json()
    assert payload['ok'] is True
    assert payload['version'] == '4.35.19'
    assert payload['contract'] == 'comparative-scenario-model-assurance'
    assert 'unit' in payload['comparison_dimensions']
    assert payload['method_card_count'] >= 2
    assert any('No silent' in item for item in payload['boundaries'])


def test_comparison_assurance_blocks_direct_difference_on_unit_or_period_mismatch():
    payload = CLIENT.post('/public/assurance/comparison', json={
        'baseline_period': '2023',
        'reference_period': '2024',
        'records': [
            {'id': 'a', 'geography': 'BRA', 'indicator': 'energy', 'value': 10, 'unit': 'PJ', 'definition_id': 'energy-v1', 'period': '2023', 'frequency': 'A'},
            {'id': 'b', 'geography': 'IND', 'indicator': 'energy', 'value': 12, 'unit': 'TWh', 'definition_id': 'energy-v1', 'period': '2024', 'frequency': 'A'},
        ],
    }).json()
    assert payload['summary']['review_required'] == 1
    review = payload['reviews'][0]
    assert review['direct_difference_allowed'] is False
    assert review['dimensions']['unit']['match'] is False
    assert review['dimensions']['period']['match'] is False
    assert payload['silent_normalization'] is False
    assert payload['imputation'] is False


def test_comparison_assurance_allows_explicitly_compatible_records():
    payload = ComparativeModelAssuranceCenter(Settings()).comparison({
        'records': [
            {'geography': 'BRA', 'indicator': 'population', 'value': 1, 'unit': 'people', 'definition_id': 'wb-pop', 'period': '2023', 'frequency': 'A', 'price_basis': 'n/a', 'seasonal_adjustment': 'n/a'},
            {'geography': 'IND', 'indicator': 'population', 'value': 2, 'unit': 'people', 'definition_id': 'wb-pop', 'period': '2023', 'frequency': 'A', 'price_basis': 'n/a', 'seasonal_adjustment': 'n/a'},
        ]
    })
    assert payload['reviews'][0]['state'] == 'compatible'
    assert payload['reviews'][0]['direct_difference_allowed'] is True
    assert len(payload['fingerprint']) == 64


def test_scenario_assurance_builds_assumption_ledger_and_nonprobabilistic_envelope():
    response = CLIENT.post('/public/assurance/scenario', json={
        'baseline': 100,
        'baseline_label': 'Illustrative baseline',
        'baseline_period': '2025',
        'unit': 'index',
        'assumptions': [
            {'id': 'demand', 'label': 'Demand change', 'mode': 'percent', 'low': -5, 'base': 10, 'high': 20, 'rationale': 'User supplied'},
            {'id': 'fixed', 'label': 'Fixed addition', 'mode': 'absolute', 'low': 0, 'base': 5, 'high': 10},
        ],
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['base_outcome'] == 115.0
    assert len(payload['ledger']) == 2
    assert len(payload['sensitivity']) == 2
    assert payload['uncertainty_envelope']['probabilistic'] is False
    assert payload['uncertainty_envelope']['confidence_interval'] is False
    assert payload['methodology']['forecast'] is False
    assert len(payload['fingerprint']) == 64


def test_scenario_assurance_rejects_missing_baseline():
    response = CLIENT.post('/public/assurance/scenario', json={'assumptions': []})
    assert response.status_code == 400


def test_model_card_review_requires_explicit_use_limits_validation_and_provenance():
    incomplete = CLIENT.post('/public/assurance/model-review', json={'model_id': 'm1', 'title': 'Model'}).json()
    assert incomplete['state'] == 'review_required'
    assert 'limitations' in incomplete['missing_fields']
    complete = CLIENT.post('/public/assurance/model-review', json={
        'model_id': 'm1', 'title': 'Model', 'model_version': '1',
        'intended_use': 'Research comparison', 'limitations': 'Not causal',
        'prohibited_uses': ['Autonomous decisions'], 'inputs': ['indicator A'], 'outputs': ['estimate'],
        'uncertainty': 'Interval supplied by source', 'validation': 'Held-out evaluation', 'provenance': 'Published source registry'
    }).json()
    assert complete['complete'] is True
    assert complete['state'] == 'complete'
    assert 'does not establish predictive validity' in complete['statement']


def test_model_review_flags_autonomous_decision_authority():
    payload = CLIENT.post('/public/assurance/model-review', json={
        'model_id': 'm2', 'title': 'Model', 'model_version': '1', 'intended_use': 'Research', 'limitations': 'Limited',
        'prohibited_uses': ['None'], 'inputs': ['x'], 'outputs': ['y'], 'uncertainty': 'unknown', 'validation': 'documented', 'provenance': 'source',
        'autonomous_decision_authority': True,
    }).json()
    assert payload['state'] == 'review_required'
    assert payload['boundary_flags']


def test_public_model_cards_include_nonpredictive_method_cards():
    payload = CLIENT.get('/public/assurance/model-cards').json()
    assert payload['ok'] is True
    assert payload['method_card_count'] >= 2
    ids = {item['model_id'] for item in payload['cards']}
    assert 'transparent-arithmetic-scenario' in ids
    assert 'comparison-compatibility-review' in ids


def test_reproducible_assurance_package_has_stable_digest():
    request = {
        'title': 'Assurance packet',
        'comparison': {'records': [
            {'geography': 'BRA', 'indicator': 'x', 'value': 1, 'unit': 'index', 'definition_id': 'v1', 'period': '2025', 'frequency': 'A', 'price_basis': 'n/a', 'seasonal_adjustment': 'n/a'},
            {'geography': 'IND', 'indicator': 'x', 'value': 2, 'unit': 'index', 'definition_id': 'v1', 'period': '2025', 'frequency': 'A', 'price_basis': 'n/a', 'seasonal_adjustment': 'n/a'}
        ]},
        'scenario': {'baseline': 10, 'assumptions': [{'id': 'a', 'mode': 'percent', 'base': 10, 'low': 5, 'high': 15}]}
    }
    first = CLIENT.post('/public/assurance/package', json=request).json()
    second = CLIENT.post('/public/assurance/package', json=request).json()
    assert first['integrity']['digest'] == second['integrity']['digest']
    assert len(first['integrity']['digest']) == 64
    assert first['integrity']['meaning'].startswith('content-change')


def test_v3260_assets_are_shipped_to_application_and_wordpress():
    html = (ROOT / 'backend/public_app/index.html').read_text()
    worker = (ROOT / 'backend/public_app/service-worker.js').read_text()
    assert 'assurance-v3260.css?v=4.35.19' in html
    assert 'assurance-v3260.js?v=4.35.19' in html
    assert 'assurance-v3260.js' in worker
    for name in ('assurance-v3260.js', 'assurance-v3260.css'):
        assert (ROOT / 'backend/public_app/assets' / name).read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets' / name).read_bytes()
