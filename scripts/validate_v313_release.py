from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.1.3"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_v313.py': [
        'SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.3"',
        'DEFAULT_SIGNAL_LIMIT = 16', 'MAX_SIGNAL_LIMIT = 24',
        'DEFAULT_MAX_SIGNALS_PER_SOURCE = 2', 'MAX_CONFIGURABLE_SIGNALS_PER_SOURCE = 5',
        'FEED_REGISTRY = {', 'DEFAULT_FEEDS = (', 'feed_selection_supported": True',
        'requested_feeds', 'excluded_feeds', 'active_feeds', 'feed_id',
    ],
    'backend/app/main.py': [
        'from .live_intelligence_v313 import',
        'feeds: str = Query(default="", max_length=320)',
        'exclude: str = Query(default="", max_length=320)',
        'max_per_source: int = Query(default=2, ge=1, le=5)',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.1.3', "const VERSION = '3.1.3';",
        "'live_intelligence_feeds' =>", "'live_intelligence_max_per_source' => '2'",
        "'live_intelligence_shortcode_overrides' => '1'", 'Displayed feeds',
        'inject_live_intelligence_content_fallback', '$this->live_intelligence_rendered',
        'data-feeds', 'data-exclude', 'data-max-per-source',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': [
        'new URLSearchParams', "params.set('feeds', feeds)", "params.set('exclude', exclude)",
        'max_per_source', 'Math.min(24',
    ],
    'README.md': ['v3.1.3 — Feed Selection and Placement Reliability Repair', 'Current release:** v3.1.3'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')

php = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text(encoding='utf-8')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text(encoding='utf-8')
if 'scsi-live-intelligence-parchment-navigation' in css or 'Navigation surface</th>' in php:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')

policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V313.json').read_text(encoding='utf-8'))
for key in [
    'administrator_feed_selection', 'automatic_ticker_uses_saved_feeds',
    'shortcode_feed_inclusion', 'shortcode_feed_exclusion', 'shortcode_source_limit',
    'shortcode_override_governance', 'canonical_feed_ids_returned', 'feed_state_reporting',
    'category_balancing', 'duplicate_suppression', 'placement_render_guard',
    'below_breadcrumb_content_fallback', 'below_header_mode', 'shortcode_only_mode',
    'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
    'hover_pause_supported', 'focus_pause_supported', 'pause_button_supported',
    'last_verified_feed_preserved_on_refresh_failure',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in [
    'platform_status_default', 'raw_upstream_payloads_exposed', 'browser_api_keys_exposed',
    'demonstration_values_public', 'automatic_interpretation', 'sticky_ticker_default', 'sitewide_default',
]:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
if policy.get('available_feed_count') != 8 or policy.get('wordpress_default_feed_count') != 7:
    raise SystemExit('Feed-count policy mismatch.')
if policy.get('default_signal_limit') != 16 or policy.get('maximum_signal_limit') != 24:
    raise SystemExit('Signal-limit policy mismatch.')
if policy.get('default_maximum_signals_per_source') != 2 or policy.get('maximum_configurable_signals_per_source') != 5:
    raise SystemExit('Source-limit policy mismatch.')
print('Site Intelligence v3.1.3 release contract passed.')
