#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.21.0"', 'RELEASE_NAME = "Scheduled Monitoring, Digests, and Public Intelligence Feeds"'],
    "backend/app/config.py": ["scheduled_monitoring_enabled", "scheduled_monitoring_monitors_path", "scheduled_monitoring_digests_path", "scheduled_monitoring_feeds_path"],
    "backend/app/scheduled_monitoring_v2210.py": ['RELEASE_VERSION = "2.21.0"', "def save_monitor(", "def check_monitor(", "def run_due(", "def generate_digest(", "def feed_payload(", "def deliver_digest("],
    "backend/app/main.py": ['"/public/scheduled-monitoring"', '"/public/intelligence-digests"', '"/public/intelligence-feeds/{feed_id}"', '"/admin/scheduled-monitoring/run-due"'],
    "backend/data/scheduled_monitoring_policy_v2210.json": ['"version": "2.21.0"', "Duplicate alerts", "human explicitly approves", "disabled by default"],
    "backend/public_app/index.html": ['data-route="monitoring"', 'id="scheduledMonitoringStudio"', '/app/assets/monitoring-v2210.js?v=2.21.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.21.0"', 'monitoring:[', 'window.SCScheduledMonitoringV2210'],
    "backend/public_app/assets/monitoring-v2210.js": ['const VERSION="2.21.0"', 'window.SCScheduledMonitoringV2210', '/public/intelligence-feeds'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.21.0"', '"/app/assets/monitoring-v2210.css"', '"/app/assets/monitoring-v2210.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.21.0', 'sc_public_monitoring_digests', 'sc_scheduled_monitoring_control_center', 'sc_public_intelligence_feed'],
    "scripts/scheduled_monitoring_v2210.py": ["summary", "run-due", "digest"],
    "docs/V2210_SCHEDULED_MONITORING_DIGESTS_PUBLIC_INTELLIGENCE_FEEDS.md": ["dry_run=true", "human explicitly approves", "No match does not prove"],
    "docs/RELEASE_MANIFEST_V2210.json": ['"release": "2.21.0"', '"persistent_scheduler_claimed": false', '"hosted_subscriber_profile_required": false', '"automatic_publication": false'],
    "README.md": ["Current release:** v2.21.0 — Scheduled Monitoring, Digests, and Public Intelligence Feeds", "/app/?view=monitoring"],
    "CHANGELOG.md": ["## 2.21.0 — Scheduled Monitoring, Digests, and Public Intelligence Feeds"],
}

errors = []
for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        errors.append(f"missing {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"{relative}: missing {marker}")

manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2210.json").read_text(encoding="utf-8"))
for key in ["human_digest_approval_required", "deduplication_receipts", "delivery_recipient_redaction"]:
    if manifest.get(key) is not True:
        errors.append(f"governance manifest {key} must be true")
for key in ["persistent_scheduler_claimed", "hosted_subscriber_profile_required", "subscriber_tracking", "automatic_emergency_dispatch", "automatic_publication", "individual_tracking"]:
    if manifest.get(key) is not False:
        errors.append(f"governance manifest {key} must be false")

runtime = [
    ROOT / "backend/data/scheduled_monitoring_v2210",
    ROOT / "backend/data/intelligence_publishing_v2200",
    ROOT / "backend/data/knowledge_graph_v2190",
    ROOT / "backend/data/evidence_synthesis_v2180",
    ROOT / "backend/data/model_governance_v2170",
    ROOT / "backend/data/statistical_harmonization_v2160",
    ROOT / "backend/data/spatial_evidence_v2150",
    ROOT / "backend/data/historical_archive_v2140",
]
for path in runtime:
    if path.exists():
        errors.append(f"writable runtime directory packaged: {path.relative_to(ROOT)}")

if errors:
    print("Site Intelligence v2.21.0 release contract failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)
print("Site Intelligence v2.21.0 release contract passed.")
