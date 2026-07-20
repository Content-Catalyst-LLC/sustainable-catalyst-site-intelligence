from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.1.5"', 'Connected Public Intelligence and Evidence Platform'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.1.5', "const VERSION = '3.1.5';",
        "'live_intelligence_mobile_mode' => 'rotator'",
        "'live_intelligence_mobile_interval' => '7'",
        'scsi-live-intelligence__previous', 'scsi-live-intelligence__next',
        'scsi-live-intelligence__position', 'Mobile presentation', 'Hide ticker on mobile',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': [
        'showMobileSignal', 'startRotation', 'touchstart', 'touchend', 'finePointer', 'reducedMotion',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css': [
        '@media(hover:hover) and (pointer:fine)', 'is-mobile-rotator',
        'scsi-live-intelligence__mobile-controls', 'data-mobile-mode="hidden"',
    ],
    'README.md': ['v3.1.5 — Mobile Navigation and Motion Repair', 'Current release:** v3.1.5'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V315.md': ['Previous and next buttons', 'Touch devices'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'scsi-live-intelligence-parchment-navigation' in css or 'ast-breadcrumbs-wrapper' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V315.json').read_text())
for key in ['previous_next_controls', 'swipe_navigation', 'position_counter', 'mobile_auto_advance', 'reduced_motion_disables_auto_advance', 'touch_hover_pause_prevented', 'mobile_hide_option', 'desktop_marquee_preserved', 'feed_selection_preserved', 'placement_settings_preserved', 'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched']:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['raw_upstream_payloads_exposed', 'browser_api_keys_exposed', 'automatic_interpretation']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
if policy.get('default_mobile_mode') != 'rotator' or policy.get('default_mobile_interval_seconds') != 7:
    raise SystemExit('Mobile default policy mismatch.')
print('Site Intelligence v3.1.5 release contract passed.')
