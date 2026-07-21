from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    'backend/app/version.py': ['APP_VERSION = "3.5.0"', 'Connected Public Intelligence and Evidence Platform'],
    'backend/app/live_intelligence_context_v340.py': [
        'build_signal_context', 'build_signal_evidence', 'render_signal_context_html',
        'canonical_digest', 'related_research', 'independent verification',
    ],
    'backend/app/live_intelligence_v314.py': [
        'signal_context_supported', 'signal_evidence_download_supported',
        'signal_timeline_supported', 'decision_studio_handoff_supported', 'enrich_signal_links',
    ],
    'backend/app/main.py': [
        '/public/live-intelligence/context-policy', '/public/live-intelligence/signals/{signal_id}',
        'public_live_intelligence_signal_context_view_endpoint',
    ],
    'backend/app/config.py': ['live_intelligence_context_enabled'],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php': [
        'Version: 3.5.0', "const VERSION = '3.5.0';", 'scsi_live_signal',
        'render_live_intelligence_signal_page', 'live_intelligence_detail_links', 'Send to Decision Studio',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js': [
        'contextBase', 'data-scsi-signal-id', 'sc_live_intelligence_context_open',
    ],
    'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css': [
        'scsi-live-signal-context', 'scsi-live-signal-button',
    ],
    'README.md': ['v3.5.0 — Signal Context and Drill-Down', 'Current release:** v3.5.0'],
    'RELEASE_NOTES_SITE_INTELLIGENCE_V340.md': ['Source lineage', 'SHA-256', 'Decision Studio'],
    'docs/V340_SIGNAL_CONTEXT_DRILL_DOWN.md': ['Context contract', 'Non-claims'],
    'docs/live-intelligence-context-v340.schema.json': ['sc-site-intelligence-live-signal-context/1.0'],
}
for rel, markers in checks.items():
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise SystemExit(f'{rel}: missing {marker}')
policy = json.loads((ROOT / 'docs/RELEASE_MANIFEST_V340.json').read_text())
for key in [
    'public_signal_context', 'source_lineage', 'signal_timeline',
    'map_context_when_coordinates_exist', 'related_workspace_routes',
    'bounded_research_suggestions', 'downloadable_evidence_records',
    'canonical_sha256_digest', 'wordpress_signal_detail_routes',
    'site_intelligence_handoff', 'decision_studio_handoff',
    'feed_controls_preserved', 'source_operations_preserved',
    'event_clustering_preserved', 'transparent_ranking_preserved',
    'mobile_rotator_preserved', 'placement_reliability_preserved',
    'theme_navigation_styles_untouched', 'breadcrumb_styles_untouched',
]:
    if policy.get(key) is not True:
        raise SystemExit(f'Release policy requires {key}=true')
for key in [
    'independent_verification_claimed', 'causal_inference',
    'geographic_precision_inflation', 'automatic_publication',
    'truth_certification', 'browser_api_keys_exposed',
]:
    if policy.get(key) is not False:
        raise SystemExit(f'Release policy requires {key}=false')
css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
if 'ast-breadcrumbs-wrapper' in css or 'scsi-live-intelligence-parchment-navigation' in css:
    raise SystemExit('Theme navigation or breadcrumb color overrides must remain absent.')
manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
if manifest.get('release') != '3.5.0':
    raise SystemExit('Immutable manifest release mismatch.')
print('Site Intelligence v3.5.0 release contract passed.')
