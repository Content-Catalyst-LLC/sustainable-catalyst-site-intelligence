from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.5.0"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_channels_v350.py': ['CHANNEL_REGISTRY', 'channel_directory', 'filter_channel_signals', 'silent_global_fallback'],
    'backend/app/main.py': ['/public/live-intelligence/channels', '/public/live-intelligence/channel-policy', 'public_live_intelligence_channel_feed_endpoint'],
    'backend/app/config.py': ['live_intelligence_channels_enabled'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': ['Version: 3.5.0', "const VERSION = '3.5.0';", 'live_intelligence_channel', 'live_intelligence_region', 'live_intelligence_country'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': ['root.dataset.channel', "params.set('region'", "params.set('country'"],
    'README.md': ['v3.5.0 — Topic and Regional Channels', 'Current release:** v3.5.0'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V350.md': ['Topic channels', 'Regional channels', 'empty'],
    'docs/V350_TOPIC_REGIONAL_CHANNELS.md': ['Channel contract', 'Empty results'],
    'docs/live-intelligence-channels-v350.schema.json': ['sc-site-intelligence-live-intelligence-channels/1.0'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V350.json').read_text())
for key in ['topic_channels','regional_channels','country_filters','channel_directory','shortcode_channel_overrides','empty_result_honesty','feed_controls_preserved','source_operations_preserved','event_clustering_preserved','transparent_ranking_preserved','signal_context_preserved','mobile_rotator_preserved','placement_reliability_preserved','theme_navigation_styles_untouched','breadcrumb_styles_untouched']:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['silent_global_fallback','coordinate_only_country_inference','geopolitical_judgment','truth_certification','browser_api_keys_exposed']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
if manifest.get('release') != '3.5.0':
    raise SystemExit('Immutable manifest release mismatch.')
print('Site Intelligence v3.5.0 release contract passed.')
