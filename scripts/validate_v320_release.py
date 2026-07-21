from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.5.0"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_source_operations_v320.py': [
        'LiveIntelligenceSourceOperations', 'source_enablement', 'manual_test',
        'license', 'coverage', 'requests_today', 'consecutive_failures',
    ],
    'backend/app/live_intelligence_v314.py': [
        'source_operations_supported', 'LiveIntelligenceSourceOperations', 'record_operations', 'source_priority',
    ],
    'backend/app/main.py': [
        '/public/live-intelligence/sources', '/admin/live-intelligence/sources/control-center',
        '/admin/live-intelligence/sources/history', '/admin/live-intelligence/sources/{feed_id}/test',
    ],
    'backend/app/config.py': [
        'live_source_operations_registry_path', 'live_source_operations_state_path',
        'live_source_operations_history_path',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.5.0', "const VERSION = '3.5.0';", 'Signal source operations',
        'rest_live_intelligence_sources', 'rest_live_intelligence_source_update',
        'rest_live_intelligence_source_test', 'scsi-source-operations-table',
    ],
    'README.md': ['v3.5.0 — Signal Source Operations', 'Current release:** v3.5.0'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V320.md': ['public-safe source metadata', 'Manual live tests'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
registry = json.loads((ROOT / 'backend/data/live_intelligence_source_registry_v320.json').read_text())
if registry.get('schema') != 'sc-site-intelligence-live-source-registry/1.0':
    raise SystemExit('Source registry schema mismatch.')
if registry.get('version') != '3.5.0' or len(registry.get('sources', [])) != 8:
    raise SystemExit('Source registry release or source count mismatch.')
for source in registry['sources']:
    for key in ['feed_id', 'label', 'provider', 'category', 'collector', 'rate_limit', 'license', 'coverage', 'quality', 'public_note']:
        if key not in source:
            raise SystemExit(f"Source {source.get('feed_id')} missing {key}")
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V320.json').read_text())
for key in [
    'public_source_registry', 'protected_source_control_center', 'source_enablement',
    'source_priority', 'refresh_policy', 'cache_policy', 'rate_tracking',
    'last_success_tracking', 'failure_history', 'manual_configuration_test',
    'manual_live_test', 'license_attribution_metadata', 'geographic_temporal_coverage',
    'data_quality_status', 'wordpress_admin_dashboard', 'feed_selection_preserved',
    'mobile_rotator_preserved', 'placement_reliability_preserved',
    'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['raw_upstream_payloads_exposed', 'browser_api_keys_exposed', 'automatic_source_accuracy_certification']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
print('Site Intelligence v3.5.0 release contract passed.')
