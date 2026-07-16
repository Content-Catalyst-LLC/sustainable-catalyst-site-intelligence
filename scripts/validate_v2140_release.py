#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    "backend/app/version.py": [
        'APP_VERSION = "2.14.0"',
        'RELEASE_NAME = "Historical Archive and Temporal Change Intelligence"',
    ],
    "backend/app/config.py": [
        "historical_archive_enabled",
        "historical_archive_capture_on_ingest",
        "historical_archive_root_path",
        "historical_archive_default_retention_days",
        "historical_archive_material_change_ratio",
    ],
    "backend/app/historical_archive_v2140.py": [
        'SCHEMA_VERSION = "sc-site-intelligence-historical-archive/1.0"',
        'SNAPSHOT_SCHEMA = "sc-site-intelligence-dataset-snapshot/1.0"',
        'CHANGE_SCHEMA = "sc-site-intelligence-temporal-change/1.0"',
        'REVISION_SCHEMA = "sc-site-intelligence-source-revision/1.0"',
        'RELEASE_VERSION = "2.14.0"',
        "def capture_ingestion(",
        "def capture_snapshot(",
        "def compare_snapshots(",
        "def retention(",
        "def restore_preview(",
        "def public_summary(",
        "def control_center(",
    ],
    "backend/app/connector_operations_v2130.py": [
        'RELEASE_VERSION = "2.14.0"',
        'receipt["historical_archive"]',
        "HistoricalArchiveCenter",
    ],
    "backend/app/main.py": [
        '"/public/history"',
        '"/public/history/datasets"',
        '"/public/history/datasets/{dataset_id}/series"',
        '"/public/history/changes"',
        '"/public/history/revisions"',
        '"/admin/history/control-center"',
        '"/admin/history/snapshots/capture"',
        '"/admin/history/compare"',
        '"/admin/history/retention/apply"',
    ],
    "backend/data/historical_archive_policy_v2140.json": [
        '"version": "2.14.0"',
        '"public_payload_access": false',
        "Identical payload digests are deduplicated",
        "Restoration remains preview-only",
    ],
    "backend/tests/test_historical_archive_temporal_change_v2140.py": [
        "test_initial_snapshot_duplicate_deduplication_and_revision_detection",
        "test_temporal_change_records_numeric_deltas_without_imputation",
        "test_retention_is_preview_first_and_preserves_newest_snapshots",
        "test_connector_acceptance_creates_historical_snapshot_receipt",
    ],
    "backend/tests/test_historical_archive_release_contract_v2140.py": [
        "test_v2140_policy_and_release_manifest_preserve_public_archive_boundaries",
        "test_v2140_runtime_archive_is_not_part_of_the_source_release",
    ],
    "scripts/historical_archive_v2140.py": [
        "datasets",
        "snapshots",
        "capture",
        "export",
        "retention",
        "--apply",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 2.14.0",
        "sc_public_temporal_intelligence",
        "sc_historical_archive_control_center",
        "public-temporal-intelligence",
        "public/history",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "temporal-intelligence",
        "/public-temporal-intelligence",
    ],
    "docs/V2140_HISTORICAL_ARCHIVE_TEMPORAL_CHANGE_INTELLIGENCE.md": [
        "Versioned snapshots across all 14 managed connector datasets",
        "Source revisions versus real-world change",
        "restoration previews",
        "persistent disk",
    ],
    "docs/RELEASE_MANIFEST_V2140.json": [
        '"managed_dataset_count": 14',
        '"automatic_capture_on_accepted_ingestion": true',
        '"public_payload_access": false',
        '"restore_applies_live_state": false',
        '"retention_dry_run_default": true',
    ],
    "README.md": [
        "Current release:** v2.14.0",
        "/public/history",
        "historical_archive_v2140.py",
    ],
    "CHANGELOG.md": [
        "## 2.14.0 — Historical Archive and Temporal Change Intelligence",
    ],
}

for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")

policy = json.loads((ROOT / "backend/data/historical_archive_policy_v2140.json").read_text(encoding="utf-8"))
release = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2140.json").read_text(encoding="utf-8"))

if policy.get("schema") != "sc-site-intelligence-historical-archive/1.0":
    raise SystemExit("Historical archive policy schema is invalid.")
if policy.get("public_payload_access") is not False:
    raise SystemExit("Historical archive policy must prohibit public payload access.")
if policy.get("minimum_snapshots_to_keep", 0) < 2:
    raise SystemExit("Retention policy must protect at least two snapshots.")

required_public = {
    "/public/history",
    "/public/history/datasets",
    "/public/history/datasets/{dataset_id}/series",
    "/public/history/changes",
    "/public/history/revisions",
}
if not required_public.issubset(set(release.get("public_endpoints", []))):
    raise SystemExit("Historical public endpoint manifest is incomplete.")
if release.get("public_payload_access") is not False:
    raise SystemExit("Release governance must prohibit archived payload disclosure.")
if release.get("restore_applies_live_state") is not False:
    raise SystemExit("v2.14.0 restoration must remain preview-only.")
if release.get("retention_dry_run_default") is not True:
    raise SystemExit("Retention must remain dry-run by default.")
if release.get("paid_database_required") is not False or release.get("paid_archive_service_required") is not False:
    raise SystemExit("Zero-cost archive boundaries are missing.")

runtime_paths = [
    "backend/data/historical_archive_v2140",
    "backend/data/country_last_known_good.json",
    "backend/data/platform_core_queue.jsonl",
    "backend/data/connector_operations_state_v2130.json",
    "backend/data/connector_operations_history_v2130.jsonl",
    "backend/data/connector_operations_quarantine_v2130.jsonl",
]
for relative in runtime_paths:
    if (ROOT / relative).exists():
        raise SystemExit(f"Runtime artifact must not be present in the immutable release: {relative}")

print("Site Intelligence v2.14.0 release contract passed.")
