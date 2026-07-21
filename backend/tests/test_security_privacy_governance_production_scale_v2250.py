from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.production_governance_v2250 import ProductionGovernanceCenter, SlidingWindowRateLimiter


def settings(tmp_path: Path, environment: str = "development") -> Settings:
    base = Path(__file__).resolve().parents[1] / "data"
    return Settings(
        environment=environment,
        production_database_path=str(tmp_path / "governance" / "site.sqlite3"),
        production_backup_path=str(tmp_path / "governance" / "backups"),
        production_governance_policy_path=str(base / "production_governance_policy_v2250.json"),
        api_token="test-admin-token",
    )


def test_migrations_create_versioned_sqlite_schema(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    status = center.migration_status()
    assert status["current_version"] == 3
    assert status["up_to_date"] is True
    assert center.database_path.is_file()


def test_scoped_api_keys_are_hashed_and_shown_once(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    created = center.create_api_key({"label": "backup worker", "scopes": ["backup:read", "backup:write"]})
    assert created["token"].startswith("scsi_key-")
    assert created["shown_once"] is True
    listed = center.list_api_keys()[0]
    assert "token" not in listed and "secret_hash" not in listed
    assert center.verify_api_key(created["token"], "backup:write")["valid"] is True
    assert center.verify_api_key(created["token"], "privacy:write")["reason"] == "missing_scope"


def test_audit_chain_redacts_secrets_and_verifies(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    event = center.record_audit("connector.updated", "admin", "connector", "world-bank", "success", {"api_key": "secret", "safe": "visible"})
    assert event["metadata"]["api_key"] == "[redacted]"
    assert center.verify_audit_chain()["valid"] is True
    assert len(center.verify_audit_chain()["head_hash"]) == 64


def test_privacy_request_hashes_subject_and_tracks_due_date(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    row = center.create_privacy_request({"request_type": "access", "subject_reference": "person@example.com"})
    assert row["subject_reference_stored"] is False
    assert row["subject_hash"] != "person@example.com"
    updated = center.update_privacy_request(row["request_id"], {"status": "completed"})
    assert updated["status"] == "completed"


def test_retention_is_preview_first_and_confirmed(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    center.record_audit("one", "admin", "record", "1", "success", {})
    preview = center.retention_preview({"category": "audit_events", "days": 365})
    assert preview["requires_confirm"] is True and preview["automatic_deletion"] is False
    with pytest.raises(ValueError, match="confirm=true"):
        center.apply_retention({"category": "audit_events", "days": 365})
    applied = center.apply_retention({"category": "audit_events", "days": 365, "confirm": True})
    assert applied["confirmed"] is True


def test_backup_is_digest_verified_and_restore_is_preview_only(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    center.record_audit("backup.seed", "admin", "record", "1", "success", {})
    backup = center.create_backup({"label": "release"})
    assert Path(backup["archive_path"]).is_file()
    assert center.verify_backup(backup["backup_id"])["valid"] is True
    restore = center.restore_preview(backup["backup_id"])
    assert restore["database_mutated"] is False
    assert restore["automatic_restore"] is False


def test_persistent_job_queue_leases_and_completes(tmp_path):
    center = ProductionGovernanceCenter(settings(tmp_path))
    queued = center.enqueue_job({"job_type": "connector.refresh", "payload": {"token": "hidden", "dataset": "climate"}})
    assert queued["payload"]["token"] == "[redacted]"
    leased = center.lease_job("worker-1")
    assert leased and leased["status"] == "leased" and leased["attempts"] == 1
    completed = center.complete_job(queued["job_id"], {"status": "completed", "result": {"records": 10}})
    assert completed["status"] == "completed"
    assert center.queue_summary()["distributed"] is False


def test_local_rate_limiter_does_not_claim_distributed_enforcement():
    now = [100.0]
    limiter = SlidingWindowRateLimiter(2, 60, now_fn=lambda: now[0])
    assert limiter.check("a")["allowed"] is True
    assert limiter.check("a")["allowed"] is True
    blocked = limiter.check("a")
    assert blocked["allowed"] is False and blocked["distributed"] is False


def test_public_boundary_and_admin_api_contracts(tmp_path):
    current = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: current
    try:
        client = TestClient(app)
        public = client.get("/public/production-governance")
        assert public.status_code == 200 and public.json()["version"] == "3.11.0"
        assert "api_keys" not in public.json()["diagnostics"]["counts"]
        control = client.get("/admin/production-governance/control-center")
        assert control.status_code == 200
        key = client.post("/admin/production-governance/api-keys", json={"label": "reviewer", "scopes": ["governance:read"]})
        assert key.status_code == 200 and key.json()["shown_once"] is True
        privacy = client.post("/admin/production-governance/privacy-requests", json={"request_type": "export", "subject_reference": "case-123"})
        assert privacy.status_code == 200
        job = client.post("/admin/production-governance/jobs", json={"job_type": "backup.verify"})
        assert job.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_production_requires_token_for_admin_contract(tmp_path):
    current = settings(tmp_path, environment="production")
    app.dependency_overrides[get_settings] = lambda: current
    try:
        client = TestClient(app)
        assert client.get("/admin/production-governance/control-center").status_code == 401
        assert client.get("/admin/production-governance/control-center", headers={"X-SC-Intelligence-Token": "test-admin-token"}).status_code == 200
    finally:
        app.dependency_overrides.clear()
