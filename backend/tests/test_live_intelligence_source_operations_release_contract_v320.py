from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v320_release_contract_files_and_version_parity():
    version = (ROOT / "backend/app/version.py").read_text()
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    assert 'APP_VERSION = "3.9.0"' in version
    assert "Version: 3.9.0" in php and "const VERSION = '3.9.0';" in php
    for route in [
        '/public/live-intelligence/sources',
        '/admin/live-intelligence/sources/control-center',
        '/admin/live-intelligence/sources/history',
        '/admin/live-intelligence/sources/{feed_id}/test',
    ]:
        assert route in main


def test_v320_release_policy_preserves_existing_ticker_contracts():
    policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V320.json").read_text())
    for key in [
        "public_source_registry", "protected_source_control_center", "source_enablement",
        "source_priority", "refresh_policy", "cache_policy", "rate_tracking",
        "last_success_tracking", "failure_history", "manual_configuration_test",
        "manual_live_test", "license_attribution_metadata", "geographic_temporal_coverage",
        "data_quality_status", "wordpress_admin_dashboard", "feed_selection_preserved",
        "mobile_rotator_preserved", "placement_reliability_preserved",
        "theme_navigation_styles_untouched", "breadcrumb_styles_untouched",
    ]:
        assert policy[key] is True
    for key in ["raw_upstream_payloads_exposed", "browser_api_keys_exposed", "automatic_source_accuracy_certification"]:
        assert policy[key] is False


def test_v320_manifest_builder_excludes_writable_source_operations_state():
    builder = (ROOT / "scripts/build_v320_manifest.py").read_text()
    assert "live_intelligence_source_operations_state_v320.json" in builder
    assert "live_intelligence_source_operations_history_v320.jsonl" in builder
    assert "MANIFEST.json" in builder
