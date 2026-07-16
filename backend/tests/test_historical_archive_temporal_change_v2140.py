from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.connector_operations_v2130 import ConnectorOperationsCenter
from app.historical_archive_v2140 import HistoricalArchiveCenter, SCHEMA_VERSION
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "backend/data/historical_archive_policy_v2140.json"
REGISTRY = ROOT / "backend/data/connector_operations_registry_v2130.json"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs) -> None:
        self.value += timedelta(**kwargs)


def _settings(tmp_path: Path, **overrides) -> Settings:
    archive = tmp_path / "archive"
    values = {
        "version": "2.25.0",
        "historical_archive_policy_path": str(POLICY),
        "historical_archive_root_path": str(archive),
        "historical_archive_index_path": str(archive / "snapshot_index_v2140.jsonl"),
        "historical_archive_change_path": str(archive / "change_events_v2140.jsonl"),
        "historical_archive_revision_path": str(archive / "revision_events_v2140.jsonl"),
        "historical_archive_retention_log_path": str(archive / "retention_events_v2140.jsonl"),
        "connector_operations_registry_path": str(REGISTRY),
        "connector_operations_state_path": str(tmp_path / "connector-state.json"),
        "connector_operations_history_path": str(tmp_path / "connector-history.jsonl"),
        "connector_operations_quarantine_path": str(tmp_path / "connector-quarantine.jsonl"),
        "connector_operations_retry_backoff_seconds": 0,
    }
    values.update(overrides)
    return Settings(**values)


def test_initial_snapshot_duplicate_deduplication_and_revision_detection(tmp_path):
    clock = Clock()
    center = HistoricalArchiveCenter(_settings(tmp_path), now_fn=clock)
    first = center.capture_snapshot(
        dataset_id="climate-series",
        connector_id="nasa_power",
        payload={"source": "NASA", "source_timestamp": "2026-07-01T00:00:00Z", "indicators": [{"value": 10.0}]},
    )
    assert first["status"] == "initial_snapshot" and first["snapshot_created"] is True

    duplicate = center.capture_snapshot(
        dataset_id="climate-series",
        connector_id="nasa_power",
        payload={"source": "NASA", "source_timestamp": "2026-07-01T00:00:00Z", "indicators": [{"value": 10.0}]},
    )
    assert duplicate["status"] == "unchanged" and duplicate["deduplicated"] is True

    clock.advance(hours=1)
    revision = center.capture_snapshot(
        dataset_id="climate-series",
        connector_id="nasa_power",
        payload={"source": "NASA", "source_timestamp": "2026-07-01T00:00:00Z", "indicators": [{"value": 11.5}]},
    )
    assert revision["status"] == "source_revision"
    assert revision["change_id"] and revision["revision_id"]
    assert center.snapshots(dataset_id="climate-series")["count"] == 2
    assert center.changes(dataset_id="climate-series")["count"] == 1
    assert center.revisions(dataset_id="climate-series")["count"] == 1


def test_temporal_change_records_numeric_deltas_without_imputation(tmp_path):
    clock = Clock()
    center = HistoricalArchiveCenter(_settings(tmp_path), now_fn=clock)
    first = center.capture_snapshot(dataset_id="energy", connector_id="eia_energy", payload={"source_timestamp": "2026-07-01T00:00:00Z", "price": 100, "records": [{"id": "a"}]})
    clock.advance(days=1)
    second = center.capture_snapshot(dataset_id="energy", connector_id="eia_energy", payload={"source_timestamp": "2026-07-02T00:00:00Z", "price": 125, "records": [{"id": "a"}, {"id": "b"}]})
    comparison = center.compare_snapshots(first["snapshot_id"], second["snapshot_id"])
    price = next(item for item in comparison["numeric_changes"] if item["path"] == "price")
    assert price["delta"] == 25
    assert price["percent_change"] == 25
    assert comparison["changed"] is True


def test_dataset_temporal_coverage_and_historical_series(tmp_path):
    clock = Clock()
    center = HistoricalArchiveCenter(_settings(tmp_path), now_fn=clock)
    for day, value in [(1, 4.0), (2, 5.5), (3, 7.0)]:
        center.capture_snapshot(
            dataset_id="water",
            connector_id="world_bank",
            payload={"source_timestamp": f"2026-07-0{day}T00:00:00Z", "metric": {"value": value}, "records": [{"v": value}]},
        )
        clock.advance(days=1)
    datasets = center.datasets()
    row = datasets["datasets"][0]
    assert row["snapshot_count"] == 3
    assert row["source_period_start"].startswith("2026-07-01")
    assert row["source_period_end"].startswith("2026-07-03")
    series = center.series("water", metric="metric.value")
    assert [item["value"] for item in series["observations"]] == [4.0, 5.5, 7.0]
    assert "metric.value" in series["available_metrics"]


def test_snapshot_payloads_are_redacted_and_digest_verified(tmp_path):
    center = HistoricalArchiveCenter(_settings(tmp_path))
    result = center.capture_snapshot(
        dataset_id="public-records",
        connector_id="crossref",
        payload={"source": "Crossref", "api_token": "secret-value", "nested": {"authorization": "Bearer secret", "value": 2}},
    )
    item = center.snapshot(result["snapshot_id"], include_payload=True)
    assert item["integrity_verified"] is True
    assert item["payload"]["api_token"] == "[redacted]"
    assert item["payload"]["nested"]["authorization"] == "[redacted]"
    assert "secret-value" not in json.dumps(item)
    public = center.snapshot(result["snapshot_id"], include_payload=False)
    assert "payload" not in public and "storage_path" not in public["snapshot"]


def test_retention_is_preview_first_and_preserves_newest_snapshots(tmp_path):
    clock = Clock()
    settings = _settings(tmp_path, historical_archive_default_retention_days=30, historical_archive_max_snapshots_per_dataset=2)
    center = HistoricalArchiveCenter(settings, now_fn=clock)
    for value in range(4):
        center.capture_snapshot(dataset_id="retention", connector_id="github", payload={"source_timestamp": clock().isoformat(), "value": value})
        clock.advance(days=40)
    preview = center.retention(dry_run=True, retention_days=30, max_snapshots=2)
    assert preview["candidate_count"] == 2
    assert preview["removed_count"] == 0
    applied = center.retention(dry_run=False, retention_days=30, max_snapshots=2)
    assert applied["removed_count"] == 2
    remaining = center.snapshots(dataset_id="retention")
    assert remaining["count"] == 2


def test_export_and_restore_are_verified_but_restore_is_preview_only(tmp_path):
    center = HistoricalArchiveCenter(_settings(tmp_path))
    result = center.capture_snapshot(dataset_id="archive", connector_id="openalex", payload={"source": "OpenAlex", "count": 7})
    export = center.export_bundle("archive", include_payloads=True)
    assert export["bundle"]["payloads_included"] is True
    assert export["bundle_sha256"]
    restore = center.restore_preview(result["snapshot_id"])
    assert restore["integrity_verified"] is True
    assert restore["restore_applied"] is False
    assert restore["payload"]["count"] == 7


def test_connector_acceptance_creates_historical_snapshot_receipt(tmp_path):
    settings = _settings(tmp_path)
    center = ConnectorOperationsCenter(
        settings,
        adapter_runner=lambda adapter, settings, force: {"source": "NASA", "source_timestamp": "2026-07-16T00:00:00Z", "indicators": [{"value": 1}]},
    )
    receipt = center.run_job("refresh-nasa-power", dry_run=False)
    assert receipt["status"] == "accepted"
    assert receipt["historical_archive"]["ok"] is True
    result = receipt["historical_archive"]["snapshot_results"][0]
    assert result["snapshot_created"] is True
    assert HistoricalArchiveCenter(settings).snapshots(dataset_id="climate-energy-timeseries")["count"] == 1


def test_public_summary_exposes_metadata_not_payload_bodies(tmp_path):
    center = HistoricalArchiveCenter(_settings(tmp_path))
    center.capture_snapshot(dataset_id="summary", connector_id="gbif_biodiversity", payload={"source": "GBIF", "records": [{"species": "Example"}]})
    summary = center.public_summary()
    assert summary["schema"] == SCHEMA_VERSION
    assert summary["version"] == "2.25.0"
    assert summary["counts"]["snapshots"] == 1
    assert summary["recommended_shortcode"] == "[sc_public_temporal_intelligence]"
    assert '"payload":' not in json.dumps(summary)


def test_historical_archive_routes_are_registered_and_safe(tmp_path):
    settings = _settings(tmp_path)
    center = HistoricalArchiveCenter(settings)
    captured = center.capture_snapshot(dataset_id="route-data", connector_id="world_bank", payload={"source_timestamp": "2026-07-16T00:00:00Z", "value": 3})
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        client = TestClient(app)
        for path in [
            "/public/history",
            "/public/history/datasets",
            "/public/history/changes",
            "/public/history/revisions",
            "/public/history/datasets/route-data/series?metric=value",
            "/admin/history/control-center",
            "/admin/history/snapshots",
            f"/admin/history/snapshots/{captured['snapshot_id']}",
            f"/admin/history/restore-preview/{captured['snapshot_id']}",
            "/admin/history/retention",
        ]:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
            assert response.json()["ok"] is True
        manual = client.post("/admin/history/snapshots/capture", json={"dataset_id": "manual", "connector_id": "manual", "payload": {"value": 1}})
        assert manual.status_code == 200 and manual.json()["snapshot_created"] is True
    finally:
        app.dependency_overrides.clear()
