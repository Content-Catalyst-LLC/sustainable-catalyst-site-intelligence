#!/usr/bin/env python3
from pathlib import Path
import sys
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.config import Settings
from app.main import app
from app.version import APP_VERSION
from app.authoritative_api_production_audit_v43516 import production_audit
from app.authoritative_connectors_v43515 import connector_catalog
from app.credential_configuration_v43516 import credential_readiness
from app.external_resilience_v43517 import resilience_overview, resilience_readiness
from app.release_health_v43517 import deployment_verification, source_health_policy

assert APP_VERSION == '4.35.20'
settings = Settings(_env_file=None)

# No connector reclassification in this reliability build.
audit = production_audit(settings)
summary = audit['machine_readable_summary']
assert summary['registrations'] == 112
assert summary['counts']['LIVE'] == 51
assert summary['counts']['DISCOVERY'] == 15
assert summary['counts']['AUTH_REQUIRED'] == 17
assert summary['registered_not_retrieved'] == 27
assert summary['counts']['BULK'] == 2
assert summary['counts']['STALE'] == 0

catalog = connector_catalog(settings)
assert catalog['connector_count'] == 50
assert catalog['live_connector_count'] == 31
assert catalog['discovery_connector_count'] == 11
assert catalog['auth_required_connector_count'] == 8
assert credential_readiness(settings)['ok'] is True

resilience = resilience_overview(settings)
ready = resilience_readiness(settings)
assert ready['ok'] is True
assert ready['network_calls_performed'] is False
assert ready['secret_material_exposed'] is False
assert resilience['provider_policy_count'] >= 10
assert resilience['release_blocking_upstream_health'] is False
assert resilience['telemetry']['totals']['open_circuits'] >= 0
assert ready['checks']['retry_after_supported'] is True
assert ready['checks']['stale_is_never_silently_fresh'] is True

verification = deployment_verification(settings)
assert verification['ok'] is True
assert verification['checks']['external_resilience_control_plane_ready'] is True
assert verification['checks']['upstream_failures_remain_non_blocking'] is True
assert '/public/external-resilience/readiness' in verification['required_routes']
assert len(verification['required_routes']) == 9
health = source_health_policy(settings)
assert health['external_resilience']['upstream_health_release_blocking'] is False
assert health['external_resilience']['network_calls_performed'] is False

client = TestClient(app)
for endpoint in (
    '/public/external-resilience',
    '/public/external-resilience/readiness',
    '/public/external-resilience/providers',
    '/public/deployment-verification',
    '/public/source-health-policy',
    '/public/authoritative-connectors/readiness',
    '/public/credential-configuration/readiness',
):
    response = client.get(endpoint)
    assert response.status_code == 200, endpoint

main = (ROOT / 'backend/app/main.py').read_text()
for marker in ('external_resilience_v43517', 'release_health_v43517', '/public/external-resilience/readiness'):
    assert marker in main, marker

for relative in (
    'backend/app/authoritative_connectors_v4353.py',
    'backend/app/authoritative_connectors_v4354.py',
    'backend/app/authoritative_connectors_v4355.py',
    'backend/app/authoritative_connectors_v43511.py',
    'backend/app/unified_live_events.py',
    'backend/app/connectors/advanced_external.py',
    'backend/app/connectors/external_data.py',
):
    assert 'external_resilience_v43517' in (ROOT / relative).read_text(), relative

example = (ROOT / 'backend/.env.example').read_text()
for env in (
    'SC_SI_EXTERNAL_RESILIENCE_ENABLED=',
    'SC_SI_EXTERNAL_RETRY_ATTEMPTS=',
    'SC_SI_EXTERNAL_BACKOFF_BASE_MS=',
    'SC_SI_EXTERNAL_BACKOFF_MAX_SECONDS=',
    'SC_SI_EXTERNAL_CIRCUIT_FAILURE_THRESHOLD=',
    'SC_SI_EXTERNAL_CIRCUIT_OPEN_SECONDS=',
    'SC_SI_EXTERNAL_CACHE_MAX_ENTRIES=',
):
    assert env in example, env

promotion = (ROOT / 'promote_site_intelligence_v4_35_17_to_github_and_render_macos.sh').read_text()
assert 'Deep gate:' not in promotion
assert '/public/external-resilience/readiness' in promotion
assert 'external_resilience_ready' in promotion

print('PASS: v4.35.20 Rate Limits, Retries, Caching, Backoff & Circuit Breakers release contract')
