from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_files_and_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.4.0"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/config.py": ["scheduled_monitoring_enabled", "scheduled_monitoring_monitors_path", "scheduled_monitoring_digests_path", "scheduled_monitoring_feeds_path"],
        "backend/app/scheduled_monitoring_v2210.py": ['RELEASE_VERSION = "3.4.0"', "def save_monitor(", "def check_monitor(", "def run_due(", "def generate_digest(", "def feed_payload(", "def deliver_digest("],
        "backend/app/main.py": ['"/public/scheduled-monitoring"', '"/public/intelligence-digests"', '"/public/intelligence-feeds/{feed_id}"', '"/admin/scheduled-monitoring/run-due"'],
        "backend/data/scheduled_monitoring_policy_v2210.json": ['"version": "3.4.0"', "Duplicate alerts", "human explicitly approves", "disabled by default"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, (relative, marker)


def test_writable_scheduled_monitoring_state_is_not_packaged():
    assert not (ROOT / "backend/data/scheduled_monitoring_v2210").exists()


def test_public_app_wordpress_and_offline_contract():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    feature_js = (ROOT / "backend/public_app/assets/monitoring-v2210.js").read_text(encoding="utf-8")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="monitoring"' in html and 'id="scheduledMonitoringStudio"' in html
    assert 'window.SCScheduledMonitoringV2210' in app_js and '/public/intelligence-feeds' in feature_js
    assert 'monitoring-v2210.js' in worker and 'monitoring-v2210.css' in worker
    assert 'sc_public_monitoring_digests' in php and 'sc_scheduled_monitoring_control_center' in php and 'sc_public_intelligence_feed' in php


def test_governance_policy_boundaries():
    policy = json.loads((ROOT / "backend/data/scheduled_monitoring_policy_v2210.json").read_text(encoding="utf-8"))
    assert policy["version"] == "3.4.0"
    assert policy["prohibited"]["automatic_emergency_dispatch"] is True
    assert policy["prohibited"]["individual_tracking"] is True
    assert policy["prohibited"]["automatic_publication"] is True
