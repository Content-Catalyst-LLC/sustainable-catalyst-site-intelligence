from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.5.0"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_clustering_v330.py': [
        'cluster_event_records', 'select_ranked_signals', 'selection_reasons',
        'corroboration', 'Scores rank display relevance', 'category_boundary_required',
    ],
    'backend/app/live_intelligence_v314.py': [
        'event_clustering_supported', 'transparent_ranking_supported',
        'selection_reasons_supported', 'cluster_source_count', 'policy_url',
    ],
    'backend/app/main.py': ['/public/live-intelligence/ranking-policy'],
    'backend/app/config.py': [
        'live_intelligence_clustering_enabled', 'live_intelligence_ranking_enabled',
        'live_intelligence_cluster_time_window_hours', 'live_intelligence_cluster_distance_km',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.5.0', "const VERSION = '3.5.0';",
        'live_intelligence_show_cluster_sources', 'live_intelligence_selection_context',
        'rest_live_intelligence_ranking_policy', 'Open the public ranking policy',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': [
        'cluster_source_count', 'selection_reasons', 'Selected because:', 'development_state',
    ],
    'README.md': ['v3.5.0 — Event Clustering and Intelligence Ranking', 'Current release:** v3.5.0'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V330.md': ['canonical event', 'selection reasons', 'display relevance'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V330.json').read_text())
for key in [
    'event_clustering', 'cross_source_duplicate_suppression', 'canonical_event_records',
    'cluster_source_lineage', 'transparent_ranking', 'selection_reason_explanations',
    'ranking_component_breakdown', 'development_state_labels', 'category_diversity',
    'source_caps_preserved', 'feed_controls_preserved', 'source_operations_preserved',
    'mobile_rotator_preserved', 'placement_reliability_preserved',
    'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in ['truth_scoring', 'danger_scoring', 'automatic_accuracy_certification', 'causal_inference', 'browser_api_keys_exposed']:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
if manifest.get('release') != '3.5.0':
    raise SystemExit('Immutable manifest release mismatch.')
print('Site Intelligence v3.5.0 release contract passed.')
