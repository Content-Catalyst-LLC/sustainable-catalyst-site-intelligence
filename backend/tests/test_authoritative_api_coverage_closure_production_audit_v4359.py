from __future__ import annotations
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.authoritative_api_production_audit_v4359 import closure_ledger, production_audit, production_readiness, audit_overview, workspace_matrix


def _settings():
    return Settings(_env_file=None, reliefweb_appname='', nasa_firms_map_key='', usda_nass_api_key='')


def test_production_audit_reconciles_current_inventory():
    audit=production_audit(_settings())
    s=audit['summary']
    assert s['source_registrations']==184
    assert s['machine_readable_registrations']==101
    assert s['implemented_or_configuration_gated_registrations']==66
    assert s['registered_but_not_retrieved']==45
    assert s['counts']['STALE']==0
    assert audit['machine_readable_summary']['registered_not_retrieved']==44
    assert audit['machine_readable_summary']['implemented_discovery_or_configuration_gated']==53
    assert audit['production_controls_ready'] is True
    assert audit['coverage_closure_complete'] is False
    assert audit['closure_status']=='production-controls-ready-backlog-open'


def test_coverage_percentages_are_deterministic_and_honest():
    audit=production_audit(_settings())
    coverage=audit['coverage']
    assert coverage['live_or_discovery_pct_of_machine_readable']==41.58
    assert coverage['implemented_discovery_or_configuration_gated_pct_of_machine_readable']==52.48
    assert coverage['registered_not_retrieved_pct_of_machine_readable']==43.56


def test_closure_ledger_keeps_registered_auth_bulk_and_stale_separate():
    ledger=closure_ledger(_settings())
    summary=ledger['summary']
    assert summary['registered_not_retrieved']==44
    assert summary['configuration_required']==11
    assert summary['bulk_only']==4
    assert summary['stale']==0
    assert len(ledger['ledger_sha256'])==64


def test_workspace_priority_tiers_expose_concentrated_gaps():
    ledger=closure_ledger(_settings())
    rows={r['workspace']:r for r in ledger['workspace_ledger']}
    assert rows['Energy Infrastructure & Power Systems']['priority_tier']=='HIGH'
    assert rows['Digital Connectivity']['priority_tier']=='HIGH'
    assert rows['Solid Waste & Circular Materials']['priority_tier']=='LOW'


def test_readiness_is_network_free_and_does_not_require_total_connector_completion():
    result=production_readiness(_settings())
    assert result['ok'] is True
    assert result['network_calls_performed'] is False
    assert result['coverage_closure_complete'] is False
    assert result['summary']['registered_not_retrieved']==44


def test_authoritative_api_overview_includes_production_closure_state():
    result=audit_overview(_settings())
    assert result['production_audit']['production_controls_ready'] is True
    assert result['closure_ledger']['registered_not_retrieved']==44


def test_workspace_matrix_adds_priority_tier_without_removing_prior_fields():
    result=workspace_matrix(_settings())
    assert result['workspace_count']==44
    assert all('counts' in r and 'connector_gap' in r and 'priority_tier' in r for r in result['workspaces'])


def test_public_production_audit_routes_exist():
    client=TestClient(app)
    for endpoint in ('/public/authoritative-apis/production-audit','/public/authoritative-apis/closure-ledger','/public/authoritative-apis/production-readiness'):
        response=client.get(endpoint)
        assert response.status_code==200, endpoint
        assert response.json()['version']=='4.35.12'
