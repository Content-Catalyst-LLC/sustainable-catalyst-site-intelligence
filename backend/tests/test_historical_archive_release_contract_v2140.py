from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v2140_policy_and_release_manifest_preserve_public_archive_boundaries() -> None:
    policy = json.loads((ROOT / "backend/data/historical_archive_policy_v2140.json").read_text(encoding="utf-8"))
    release = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2140.json").read_text(encoding="utf-8"))

    assert policy["schema"] == "sc-site-intelligence-historical-archive/1.0"
    assert policy["version"] == "2.14.0"
    assert policy["public_payload_access"] is False
    assert any("Restoration remains preview-only" in rule for rule in policy["rules"])

    assert release["release"] == "2.14.0"
    assert release["managed_dataset_count"] == 14
    assert release["automatic_capture_on_accepted_ingestion"] is True
    assert release["public_payload_access"] is False
    assert release["restore_applies_live_state"] is False
    assert release["retention_dry_run_default"] is True
    assert release["paid_database_required"] is False
    assert release["paid_archive_service_required"] is False


def test_v2140_wordpress_and_javascript_publish_temporal_surfaces() -> None:
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    javascript = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")

    assert "Version: 3.8.0" in plugin
    assert "sc_public_temporal_intelligence" in plugin
    assert "sc_historical_archive_control_center" in plugin
    assert "public-temporal-intelligence" in plugin
    assert "public/history" in plugin
    assert "'temporal-intelligence': '/public-temporal-intelligence'" in javascript


def test_v2140_runtime_archive_is_not_part_of_the_source_release() -> None:
    assert not (ROOT / "backend/data/historical_archive_v2140").exists()
