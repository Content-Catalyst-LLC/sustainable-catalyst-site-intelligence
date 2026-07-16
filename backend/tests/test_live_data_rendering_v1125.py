from app.cross_domain_dashboard_studio import dashboard_data, country_intelligence, cross_domain_comparison, rendering_diagnostics


def test_dashboard_payload_has_renderable_evidence():
    data = dashboard_data('climate-human-vulnerability', country='KEN')
    assert data['ok'] is True
    assert data['version'] == '2.25.0'
    assert data['rendering_state'] == 'source-aware-public-snapshot'
    assert data['evidence_items']
    assert data['source_summary']['registered_sources'] > 0
    assert all('value_status' in item for item in data['evidence_items'])


def test_country_payload_has_country_and_sources():
    data = country_intelligence('KEN')
    assert data['country_name'] == 'Kenya'
    assert len(data['evidence_items']) == 6
    assert data['source_summary']['domains'] == 6


def test_comparison_payload_has_explicit_missing_values():
    data = cross_domain_comparison('KEN', 'GHA')
    assert data['ok'] is True
    assert len(data['comparison_rows']) == 6
    assert all(row['left']['value'] is None for row in data['comparison_rows'])


def test_rendering_diagnostics_contract():
    data = rendering_diagnostics()
    assert data['ok'] is True
    assert all(check['status'] == 'pass' for check in data['checks'])
