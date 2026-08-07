from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.data_truth_control_plane_v3240 import GlobalDataTruthControlPlane, ATTENTION_STATES
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def test_control_plane_composes_all_registered_sources():
    payload = CLIENT.get('/public/data-truth/control-plane').json()
    assert payload['ok'] is True
    assert payload['version'] == '3.25.0'
    assert payload['contract'] == 'global-data-truth-control-plane'
    assert payload['source_count'] == 8
    assert sum(payload['summary'][state] for state in ATTENTION_STATES) == 8
    assert len(payload['control_plane_fingerprint']) == 64
    assert all(len(row['status_fingerprint']) == 64 for row in payload['sources'])


def test_control_plane_does_not_convert_context_or_missing_success_to_live():
    payload = CLIENT.get('/public/data-truth/control-plane').json()
    rows = {row['feed_id']: row for row in payload['sources']}
    assert all(row['presentation_state'] != 'live' or row['live_claim_allowed'] for row in rows.values())
    assert all(row['attention_state'] != 'operational' for row in rows.values() if not row['last_success_at'])
    assert rows['openalex']['presentation_state'] in {'context_only', 'unavailable', 'demonstration'}


def test_source_detail_and_unknown_source_fail_closed():
    response = CLIENT.get('/public/data-truth/control-plane/source/world_bank')
    assert response.status_code == 200
    payload = response.json()
    assert payload['source']['feed_id'] == 'world_bank'
    assert {row['country']['code'] for row in payload['country_examples']} == {'KEN', 'BRA', 'USA'}
    assert CLIENT.get('/public/data-truth/control-plane/source/not-a-source').status_code == 404


def test_history_is_explicitly_derived_and_not_claimed_complete():
    payload = CLIENT.get('/public/data-truth/control-plane/history?source=world_bank&limit=25').json()
    assert payload['contract'] == 'global-data-truth-derived-status-history'
    assert payload['source_filter'] == 'world_bank'
    assert payload['complete_event_log'] is False
    assert payload['event_count'] >= 1
    assert all(event['feed_id'] == 'world_bank' and len(event['event_id']) == 24 for event in payload['events'])


def test_schema_drift_register_requires_review_when_unobserved_or_changed():
    payload = CLIENT.get('/public/data-truth/control-plane/schema-drift').json()
    assert payload['source_count'] == 8
    assert payload['changed_count'] + payload['unobserved_count'] <= 8
    for row in payload['sources']:
        assert row['review_required'] is (row['schema_state'] in {'changed', 'not_observed'})
        assert 'silently substitute' in row['resolution_policy']


def test_outage_register_does_not_claim_upstream_global_outage():
    payload = CLIENT.get('/public/data-truth/control-plane/outages').json()
    assert payload['contract'] == 'global-data-truth-source-outage-register'
    assert payload['incident_count'] == len(payload['incidents'])
    assert all(item['automatically_resolved'] is False for item in payload['incidents'])
    assert any('not proof' in boundary.lower() for boundary in payload['boundaries'])


def test_coverage_monitor_reports_country_and_source_gaps_without_imputation():
    payload = CLIENT.get('/public/data-truth/control-plane/coverage?countries=KEN,BRA,USA').json()
    assert payload['country_count'] == 3
    assert payload['source_count'] == 8
    assert len(payload['country_gaps']) == 3
    assert len(payload['source_gaps']) == 8
    assert sum(payload['state_counts'].values()) == 24
    brazil = next(row for row in payload['country_gaps'] if row['country']['code'] == 'BRA')
    assert brazil['unresolved_source_count'] >= 1


def test_cross_workspace_truth_tracks_selected_country_dependencies():
    payload = CLIENT.get('/public/data-truth/control-plane/workspaces?country=BRA').json()
    assert payload['country']['code'] == 'BRA'
    assert payload['workspace_count'] == 12
    assert sum(payload['summary'].values()) == 12
    economics = next(row for row in payload['workspaces'] if row['workspace_id'] == 'economics')
    assert economics['dependencies'][0]['feed_id'] == 'world_bank'
    assert economics['dependencies'][0]['coverage_state'] == 'unknown'
    assert economics['truth_state'] == 'degraded'


def test_export_is_fingerprint_bound_and_contains_all_control_plane_surfaces():
    first = GlobalDataTruthControlPlane(Settings()).export(['KEN', 'BRA'], 'BRA')
    second = GlobalDataTruthControlPlane(Settings()).export(['KEN', 'BRA'], 'BRA')
    assert first['contract'] == 'global-data-truth-control-plane-export'
    assert set(first['payload']) == {'overview', 'schema_drift', 'outages', 'coverage', 'workspaces'}
    assert len(first['export_fingerprint']) == 64
    # Generated timestamps are intentionally part of a point-in-time export; individual source status fingerprints remain stable.
    assert [row['status_fingerprint'] for row in first['payload']['overview']['sources']] == [row['status_fingerprint'] for row in second['payload']['overview']['sources']]


def test_control_plane_assets_are_shipped_offline_and_match_wordpress():
    html = (ROOT / 'backend/public_app/index.html').read_text()
    worker = (ROOT / 'backend/public_app/service-worker.js').read_text()
    truth_js = (ROOT / 'backend/public_app/assets/data-truth-v32371.js').read_text()
    control_js = (ROOT / 'backend/public_app/assets/data-truth-control-plane-v3240.js').read_text()
    assert 'data-truth-control-plane-v3240.css?v=3.25.0' in html
    assert 'data-truth-control-plane-v3240.js?v=3.25.0' in html
    assert 'data-truth-control-plane-v3240.js' in worker
    assert 'data-truth-view="control"' in truth_js
    assert 'SCSIDataTruthControlPlaneV3240' in control_js
    assert '/public/data-truth/control-plane/export' in control_js
    for name in ('data-truth-control-plane-v3240.js', 'data-truth-control-plane-v3240.css'):
        assert (ROOT / 'backend/public_app/assets' / name).read_bytes() == (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets' / name).read_bytes()
