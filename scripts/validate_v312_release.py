from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
checks={
    'backend/app/version.py':['APP_VERSION = "3.1.2"','Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_v312.py':[
        'SCHEMA_VERSION = "sc-site-intelligence-live-intelligence/1.2"',
        'DEFAULT_SIGNAL_LIMIT = 16','MAX_SIGNAL_LIMIT = 24','MAX_SIGNALS_PER_SOURCE = 3',
        'LATEST OPEN RESEARCH','WORLD POPULATION GROWTH','RENEWABLE ENERGY SHARE',
        'theme_navigation_styles": "untouched"',
    ],
    'backend/app/main.py':['from .live_intelligence_v312 import','Query(default=16, ge=1, le=24)'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php':[
        'Version: 3.1.2',"const VERSION = '3.1.2';","'live_intelligence_limit' => '16'",'max="24"',
        "unset($stored_options['live_intelligence_parchment_navigation'])",
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css':[
        'v3.1.2 — Live Intelligence signal expansion; theme navigation surfaces remain untouched',
        'is-hover-paused','animation-play-state:paused!important',
    ],
    'README.md':['v3.1.2 — Navigation Surface Harmony and Signal Expansion','Current release:** v3.1.2'],
}
for rel, markers in checks.items():
    text=(ROOT/rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
php=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text(encoding='utf-8')
css=(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text(encoding='utf-8')
if 'Navigation surface</th>' in php:
    raise SystemExit('Legacy navigation-surface setting remains visible.')
if 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Legacy parchment CSS remains active.')
policy=json.loads((ROOT/'docs/RELEASE_MANIFEST_V312.json').read_text(encoding='utf-8'))
for key in [
    'category_balancing','duplicate_suppression','verified_public_interest_signals',
    'demonstration_records_suppressed','sample_connector_values_suppressed',
    'periodic_indicator_data_year_required','single_platform_status_item',
    'theme_navigation_styles_untouched','breadcrumb_styles_untouched',
    'legacy_parchment_override_removed','hover_pause_supported','focus_pause_supported',
    'pause_button_supported','last_verified_feed_preserved_on_refresh_failure',
    'below_breadcrumb_default','below_header_fallback','shortcode_only_mode','shortcode_available',
    'source_attribution_required','freshness_required',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['raw_upstream_payloads_exposed','browser_api_keys_exposed','demonstration_values_public','automatic_interpretation','sticky_ticker_default','sitewide_default']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
if policy.get('expanded_default_signal_limit') != 16 or policy.get('maximum_signal_limit') != 24 or policy.get('maximum_signals_per_source') != 3:
    raise SystemExit('Signal expansion limits do not match release policy.')
print('Site Intelligence v3.1.2 release contract passed.')
