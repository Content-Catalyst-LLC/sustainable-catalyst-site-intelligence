from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v4392_backend_and_wordpress_release_identity_match():
    version = (ROOT / 'backend/app/version.py').read_text()
    plugin = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
    assert 'APP_VERSION = "4.39.2"' in version
    assert 'EXPECTED_WORDPRESS_PLUGIN_VERSION = APP_VERSION' in version
    assert ' * Version: 4.39.2' in plugin
    assert "const VERSION = '4.39.2';" in plugin
    assert "const RELEASE_ID = 'site-intelligence-v4.39.2';" in plugin


def test_v4392_keeps_approved_homepage_entry_structure():
    plugin = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php').read_text()
    method = plugin.split('public function site_intelligence_home_shortcode', 1)[1].split('private function app_embed_url', 1)[0]
    assert "'Explore the World'" in method
    assert "'Earth & Environment'" in method
    assert "'Ocean & Space'" in method
    assert 'data-scsi-home-summary' in method
    assert 'scsi-home-summary__metrics' in method
    assert 'scsi-home-summary__signals' in method
    assert 'scsi-home-summary__entries' in method


def test_v4392_live_intelligence_fetch_and_render_failures_are_separate():
    js = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js').read_text()
    method = js.split('  function setupLiveIntelligence() {', 1)[1].split('  function setupLiveIntelligenceSubscriptions()', 1)[0]
    assert 'const safeItemHtml = function' in method
    assert 'const renderMinimalFallback = function' in method
    assert "liveAnalyticsEvent('feed_render_failure'" in method
    assert 'renderMinimalFallback(data, error);' in method
    assert '}, function (error) {' in method
    assert 'LIVE INTELLIGENCE TEMPORARILY UNAVAILABLE' in method


def test_v4392_does_not_change_site_intelligence_css_contract():
    css = (ROOT / 'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css').read_text()
    assert '.scsi-home-summary__metrics' in css
    assert '.scsi-home-summary__entries' in css
    assert '.scsi-live-intelligence__track' in css


def test_v4392_backend_health_and_build_info_report_current_identity():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    health = client.get('/health')
    assert health.status_code == 200
    assert health.json()['version'] == '4.39.2'
    build = client.get('/public/build-info')
    assert build.status_code == 200
    payload = build.json()
    assert payload['version'] == '4.39.2'
    assert payload['expected_wordpress_plugin_version'] == '4.39.2'
