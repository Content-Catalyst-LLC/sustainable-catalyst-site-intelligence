from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.connector_operations_v2130 import ConnectorOperationsCenter, SCHEMA_VERSION
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "backend/data/connector_operations_registry_v2130.json"


def _settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "version": "3.4.0",
        "connector_operations_registry_path": str(REGISTRY),
        "connector_operations_state_path": str(tmp_path / "state.json"),
        "connector_operations_history_path": str(tmp_path / "history.jsonl"),
        "connector_operations_quarantine_path": str(tmp_path / "quarantine.jsonl"),
        "connector_operations_retry_backoff_seconds": 0,
    }
    values.update(overrides)
    return Settings(**values)


def test_v2130_registry_unifies_operational_connectors_without_secret_values(tmp_path):
    center = ConnectorOperationsCenter(_settings(tmp_path))
    payload = center.registry(public=False)
    assert payload["schema"] == SCHEMA_VERSION
    assert payload["version"] == "3.4.0"
    assert payload["connector_count"] == 14
    ids = {item["connector_id"] for item in payload["connectors"]}
    assert {"nasa_power", "world_bank", "sustainable_development"}.issubset(ids)
    assert "secret-value" not in json.dumps(payload)
    assert all("credential_env_names" not in item for item in payload["connectors"])


def test_dry_run_creates_accepted_receipt_history_and_dataset_diagnostics(tmp_path):
    center = ConnectorOperationsCenter(_settings(tmp_path))
    receipt = center.run_job("refresh-nasa-power", dry_run=True)
    assert receipt["status"] == "accepted"
    assert receipt["source_state"] == "dry_run"
    assert receipt["validation"]["valid"] is True
    history = center.executions()
    assert history["count"] == 1
    assert history["executions"][0]["execution_id"] == receipt["execution_id"]
    dataset = next(item for item in center.datasets()["datasets"] if item["dataset_id"] == "climate-energy-timeseries")
    assert dataset["last_accepted_at"]
    assert dataset["freshness_state"] == "fresh"


def test_invalid_ingestion_is_quarantined_without_raw_payload_and_can_be_resolved(tmp_path):
    center = ConnectorOperationsCenter(_settings(tmp_path))
    receipt = center.run_job("refresh-nasa-power", dry_run=False, supplied_payload={"token": "secret-value", "unexpected": "x"})
    assert receipt["status"] == "quarantined"
    items = center.quarantine()["items"]
    assert len(items) == 1
    assert items[0]["raw_payload_persisted"] is False
    assert items[0]["payload_preview"]["token"] == "[redacted]"
    assert "secret-value" not in json.dumps(items)
    resolution = center.resolve_quarantine(items[0]["quarantine_id"], "reject", "Schema mismatch")
    assert resolution["resolution"]["action"] == "reject"
    assert center.quarantine(status="reject")["count"] == 1


def test_retry_failures_open_circuit_and_block_subsequent_run(tmp_path):
    def failing_adapter(adapter, settings, force):
        raise RuntimeError("upstream unavailable")

    center = ConnectorOperationsCenter(
        _settings(
            tmp_path,
            connector_operations_default_retry_attempts=1,
            connector_operations_circuit_breaker_failures=2,
            connector_operations_circuit_breaker_seconds=600,
        ),
        adapter_runner=failing_adapter,
    )
    first = center.run_job("refresh-nasa-power", dry_run=False)
    second = center.run_job("refresh-nasa-power", dry_run=False)
    third = center.run_job("refresh-nasa-power", dry_run=False)
    assert first["status"] == "failed"
    assert second["status"] == "failed"
    assert third["status"] == "blocked"
    assert third["blocked_reason"] == "circuit_open"
    assert third["attempts"] == 0


def test_due_jobs_reports_never_run_scheduled_and_conditional_jobs(tmp_path):
    fixed = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    center = ConnectorOperationsCenter(_settings(tmp_path), now_fn=lambda: fixed)
    due = center.due_jobs()
    assert due["due_count"] == 14
    assert all("schedule_due" in item["reasons"] for item in due["due_jobs"])
    assert all("stale_or_failed" in item["reasons"] for item in due["due_jobs"])


def test_public_status_is_sanitized_and_endpoint_is_available(tmp_path):
    center = ConnectorOperationsCenter(_settings(tmp_path))
    public = center.public_status()
    text = json.dumps(public)
    assert public["recommended_shortcode"] == "[sc_public_connector_operations]"
    assert "credential_env_names" not in text
    assert "requests_per_minute" not in text
    assert "payload_preview" not in text

    client = TestClient(app)
    response = client.get("/public/connectors/operations")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["version"] == "3.4.0"
    assert len(data["connectors"]) == 14


def test_admin_control_center_routes_are_registered():
    client = TestClient(app)
    for path in [
        "/admin/connectors/control-center",
        "/admin/connectors/registry",
        "/admin/connectors/jobs",
        "/admin/connectors/jobs/due",
        "/admin/connectors/executions",
        "/admin/connectors/quarantine",
        "/admin/connectors/datasets",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["ok"] is True


def test_run_due_jobs_executes_explicit_dry_run_batch(tmp_path):
    fixed = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    center = ConnectorOperationsCenter(_settings(tmp_path), now_fn=lambda: fixed)
    payload = center.run_due_jobs(dry_run=True, limit=3)
    assert payload["due_count"] == 3
    assert payload["executed_count"] == 3
    assert payload["status_counts"] == {"accepted": 3}
    assert all(item["dry_run"] is True for item in payload["executions"])
    assert "explicitly" in payload["scheduler_boundary"]


def test_quota_limit_blocks_live_run_but_force_can_override(tmp_path):
    settings = _settings(tmp_path)
    center = ConnectorOperationsCenter(settings, adapter_runner=lambda adapter, settings, force: {"source": "test", "indicators": []})
    registry = center._registry
    target = next(item for item in registry["connectors"] if item["connector_id"] == "nasa_power")
    target["quota"] = {"requests_per_minute": 1, "requests_per_day": 1}
    first = center.run_job("refresh-nasa-power", dry_run=False)
    blocked = center.run_job("refresh-nasa-power", dry_run=False)
    forced = center.run_job("refresh-nasa-power", dry_run=False, force=True)
    assert first["status"] == "accepted"
    assert blocked["status"] == "blocked" and blocked["blocked_reason"] == "quota_exceeded"
    assert forced["status"] == "accepted"


def test_run_due_endpoint_is_registered_and_safe_by_default():
    client = TestClient(app)
    response = client.post("/admin/connectors/jobs/run-due", json={"limit": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["executed_count"] <= 2
