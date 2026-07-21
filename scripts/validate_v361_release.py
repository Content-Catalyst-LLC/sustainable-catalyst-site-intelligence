#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.6.1"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_reliability_v361.py': ['RELIABILITY_SCHEMA_VERSION', 'classify_signal_freshness', 'apply_reliability_policy', 'LiveIntelligenceReliabilityStore', 'same channel, geography, source selection, and limit query'],
    'backend/app/main.py': ['/public/live-intelligence/status', 'public_live_intelligence_status_endpoint'],
    'backend/app/config.py': ['live_intelligence_reliability_enabled', 'live_intelligence_last_known_good_path', 'live_intelligence_suppress_expired_signals'],
    'backend/tests/test_live_intelligence_reliability_v361.py': ['same_query_last_known_good', 'different_query', 'honest_empty_geographic_result'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': ['Version: 3.6.1', "const VERSION = '3.6.1';", 'live_intelligence_show_freshness', 'live_intelligence_proxy_stale_hours', 'rest_live_intelligence_status'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': ['data-scsi-live-delivery', 'freshness_state', 'refreshSeconds'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css': ['v3.6.1 — Live Intelligence delivery', 'data-delivery-state="delayed"'],
    'README.md': ['v3.6.1 — Live Intelligence Reliability and Freshness', 'Current release:** v3.6.1'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V361.md': ['Same-query last-known-good', '635-test regression coverage'],
    'docs/V361_LIVE_INTELLIGENCE_RELIABILITY.md': ['Reliability contract', 'Freshness describes time, not truth'],
    'docs/live-intelligence-reliability-v361.schema.json': ['sc-site-intelligence-live-intelligence-reliability/1.0'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V361.json').read_text())
for key in [
    'canonical_pipeline_preserved', 'explicit_freshness_states', 'malformed_signal_isolation',
    'duplicate_signal_suppression', 'expired_signal_suppression', 'partial_feed_delivery',
    'same_query_last_known_good', 'honest_empty_geographic_results', 'public_health_contract',
    'wordpress_bounded_proxy_cache', 'controlled_browser_refresh', 'reduced_motion_preserved',
    'keyboard_pause_preserved', 'mobile_rotator_preserved', 'theme_navigation_styles_untouched',
    'breadcrumb_styles_untouched',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in [
    'fabricated_replacement_values', 'failed_measurements_converted_to_zero',
    'cross_query_cache_reuse', 'browser_api_keys_exposed', 'freshness_as_truth_claim',
]:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
if manifest.get('release') != '3.6.1' or manifest.get('file_count') != len(manifest.get('files') or []):
    raise SystemExit('Immutable manifest release or file count mismatch.')
print('Site Intelligence v3.6.1 release contract passed.')
