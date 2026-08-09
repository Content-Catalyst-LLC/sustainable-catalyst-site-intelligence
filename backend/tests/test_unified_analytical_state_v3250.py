from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.unified_analytical_state_v3250 import UnifiedAnalyticalStateCenter

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def test_unified_state_schema_connects_six_analytical_routes():
    payload = CLIENT.get('/public/workspaces/unified-state').json()
    assert payload['ok'] is True
    assert payload['version'] == '4.4.0'
    assert payload['contract'] == 'unified-analytical-workspace-state'
    assert payload['route_count'] == 6
    assert set(payload['routes']) == {'overview', 'global', 'country', 'compare', 'spatial', 'earth'}
    assert payload['country_catalog_count'] >= 170
    assert payload['storage'] == {'browser': 'session-and-local', 'server': False, 'account_required': False}


def test_normalization_fails_closed_for_unknown_route_and_country():
    response = CLIENT.post('/public/workspaces/unified-state/normalize', json={
        'view': 'not-a-route', 'country': 'XXX', 'compare': 'XXX', 'eventDays': 9999,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['state']['view'] == 'overview'
    assert payload['state']['country'] == 'KEN'
    assert payload['state']['compare'] != 'KEN'
    assert payload['state']['eventDays'] == 365
    assert len(payload['warnings']) >= 2
    assert len(payload['fingerprint']) == 64


def test_compare_handoff_preserves_distinct_country_pair_and_indicator():
    payload = CLIENT.post('/public/workspaces/unified-state/handoff/compare', json={
        'view': 'country', 'country': 'BRA', 'compare': 'IND', 'indicator': 'population',
        'area_id': 'ignored-in-compare-link',
    }).json()
    assert payload['contract'] == 'cross-view-analytical-handoff'
    assert payload['target'] == 'compare'
    assert payload['state']['country'] == 'BRA'
    assert payload['state']['compare'] == 'IND'
    assert payload['state']['indicator'] == 'population'
    assert 'country=BRA' in payload['path'] and 'compare=IND' in payload['path']
    assert 'indicator=population' in payload['path']
    assert 'area_id=' not in payload['path']


def test_earth_deep_link_orders_dates_and_exposes_truth_dependencies():
    payload = CLIENT.post('/public/workspaces/unified-state/deep-link?target=earth', json={
        'country': 'BRA', 'layer_id': 'vegetation-index', 'date_a': '2026-08-05', 'date_b': '2026-07-01',
    }).json()
    assert payload['target'] == 'earth'
    assert payload['state']['date_a'] == '2026-07-01'
    assert payload['state']['date_b'] == '2026-08-05'
    assert payload['truth']['country'].endswith('/BRA')
    assert payload['truth']['country_records'].endswith('/BRA')
    assert payload['snapshot'] is False and payload['portable'] is True


def test_fingerprint_is_stable_for_equivalent_state():
    center = UnifiedAnalyticalStateCenter(Settings())
    first = center.normalize({'view': 'compare', 'country': 'BRA', 'compare': 'IND', 'mapCategories': ['fire', 'storm', 'fire']})
    second = center.normalize({'compare': 'IND', 'country': 'BRA', 'view': 'compare', 'mapCategories': 'fire,storm'})
    assert first['fingerprint'] == second['fingerprint']
    assert first['state']['mapCategories'] == ['fire', 'storm']


def test_assets_are_shipped_offline_and_match_wordpress():
    html = (ROOT / 'backend/public_app/index.html').read_text()
    worker = (ROOT / 'backend/public_app/service-worker.js').read_text()
    assert 'cross-view-state-v3250.css?v=4.4.0' in html
    assert 'cross-view-state-v3250.js?v=4.4.0' in html
    assert 'cross-view-state-v3250.js' in worker
    assert 'data-scsi-release="4.4.0"' in html
    for name in ('cross-view-state-v3250.js', 'cross-view-state-v3250.css'):
        assert (ROOT / 'backend/public_app/assets' / name).read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets' / name).read_bytes()


def test_wordpress_release_bar_names_current_build():
    plugin = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
    host_js = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js').read_text()
    assert 'Version: 4.4.0' in plugin
    assert "Unified Public Intelligence Platform" in host_js
