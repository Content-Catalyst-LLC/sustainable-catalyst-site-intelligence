from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.1.5"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_v314.py': [
        'SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.4"',
        'CATEGORY_LABELS = {', 'SOURCE_SHORT_NAMES = {',
        '"economy_resources": "Economy, Energy & Resources"',
        '"source_short_name"', 'readability_controls_supported',
        'default_desktop_cycle_seconds', 'default_mobile_cycle_seconds',
    ],
    'backend/app/main.py': ['from .live_intelligence_v314 import build_live_intelligence, live_intelligence_status'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.1.5', "const VERSION = '3.1.5';",
        "'live_intelligence_speed_preset' => 'balanced'",
        "'live_intelligence_speed' => '30'", "'live_intelligence_mobile_speed' => '36'",
        "'live_intelligence_spacing' => 'balanced'", "'live_intelligence_text_limit' => '120'",
        "'live_intelligence_compact_sources' => '1'", 'Economy, Energy & Resources',
        'scsi-live-admin-preview', 'Restore readability defaults',
        'data-category-labels', 'data-text-limit', 'data-compact-sources',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': [
        'source_short_name', 'categoryLabels', 'shorten(fullValue, textLimit)', 'compactSources',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css': [
        '--scsi-live-mobile-duration', 'scsi-live-intelligence--spacing-compact',
        'scsi-live-intelligence--spacing-spacious', 'text-overflow:ellipsis',
    ],
    'README.md': ['v3.1.5 — Readability and Taxonomy Controls', 'Current release:** v3.1.5'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V314.md': ['Economy, Energy & Resources', 'separate restore action'],
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

policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V314.json').read_text(encoding='utf-8'))
for key in [
    'compact_source_names', 'editable_category_labels', 'canonical_category_ids_stable',
    'admin_preview_without_external_calls', 'readability_only_reset', 'feed_selection_preserved',
    'placement_settings_preserved', 'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
    'hover_pause_supported', 'focus_pause_supported', 'pause_button_supported',
    'reduced_motion_supported', 'full_signal_context_preserved',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['raw_upstream_payloads_exposed', 'browser_api_keys_exposed', 'automatic_interpretation']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
if policy.get('default_desktop_cycle_seconds') != 30 or policy.get('default_mobile_cycle_seconds') != 36:
    raise SystemExit('Default cycle policy mismatch.')
if policy.get('economy_resources_default_label') != 'Economy, Energy & Resources':
    raise SystemExit('Economy taxonomy policy mismatch.')
print('Site Intelligence v3.1.5 release contract passed.')
