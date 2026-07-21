#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.6.2"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_presentation_v362.py': ['PRESENTATION_SCHEMA', 'presentation_policy', 'reduced_motion_default', 'animated_viewport_live_region'],
    'backend/app/main.py': ['/public/live-intelligence/presentation-policy', 'public_live_intelligence_presentation_policy_endpoint'],
    'backend/tests/test_live_intelligence_presentation_accessibility_v362.py': ['minimum_touch_target_css_pixels', 'maxVisible', 'showCurrentSignal(currentIndex + 1, false)'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': ['Version: 3.6.2', "const VERSION = '3.6.2';", 'live_intelligence_presentation_mode', 'live_intelligence_reduced_motion_mode', 'live_intelligence_max_visible', 'data-scsi-live-announcer', 'rest_live_intelligence_presentation_policy'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': ['renderTicker', 'renderStatic', 'renderStacked', 'signalAccessibleText', 'showCurrentSignal', 'ArrowRight', '.slice(0, maxVisible)'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css': ['v3.6.2 — Live Intelligence presentation', 'is-static-mode', 'is-manual-mode', 'is-mobile-stacked', 'min-height:44px'],
    'README.md': ['v3.6.2 — Live Intelligence Presentation, Motion, and Accessibility Controls', 'Current release:** v3.6.2'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V362.md': ['642-test regression coverage', 'Automatic rotation does not announce every item'],
    'docs/V362_LIVE_INTELLIGENCE_PRESENTATION_ACCESSIBILITY.md': ['Motion is optional', 'Screen-reader announcements', '200% zoom'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V362.json').read_text())
for key in [
    'static_administrator_mode', 'manual_previous_next_mode', 'reduced_motion_static_or_manual',
    'mobile_stacked_mode', 'keyboard_navigation', 'swipe_navigation',
    'minimum_touch_target_44px', 'bounded_assistive_announcements', 'full_accessible_names',
    'no_javascript_fallback', 'forced_colors_supported', 'two_hundred_percent_zoom_supported',
    'maximum_visible_signal_control', 'public_presentation_policy',
    'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in [
    'motion_required_for_access', 'animated_viewport_live_region',
    'automatic_rotation_announcements', 'browser_api_keys_exposed',
    'source_ranking_changed_by_presentation',
]:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
php = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
if 'aria-live="polite" aria-busy="true"' in php:
    raise SystemExit('Animated ticker viewport must not be a polite live region.')
manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
if manifest.get('release') != '3.6.2' or manifest.get('file_count') != len(manifest.get('files') or []):
    raise SystemExit('Immutable manifest release or file count mismatch.')
print('Site Intelligence v3.6.2 release contract passed.')
