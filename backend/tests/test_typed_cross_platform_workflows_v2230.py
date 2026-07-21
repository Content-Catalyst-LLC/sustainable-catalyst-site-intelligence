from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from app.config import Settings, get_settings
from app.cross_platform_workflows_v2230 import CrossPlatformWorkflowCenter, SCHEMA_VERSION
from app.main import app


def settings(tmp_path: Path) -> Settings:
    root=tmp_path/"workflows"
    base=Path(__file__).resolve().parents[1]/"data"
    return Settings(cross_platform_workflows_packets_path=str(root/"packets.jsonl"),cross_platform_workflows_receipts_path=str(root/"receipts.jsonl"),cross_platform_workflows_attempts_path=str(root/"attempts.jsonl"),cross_platform_workflows_linkbacks_path=str(root/"linkbacks.jsonl"),cross_platform_workflows_queue_path=str(root/"queue.jsonl"),cross_platform_workflows_policy_path=str(base/"cross_platform_workflow_policy_v2230.json"),cross_platform_workflows_registry_path=str(base/"cross_platform_workflow_registry_v2230.json"))


def packet(c):
    return c.create_packet({"route_id":"site-intelligence-to-workbench-analysis","title":"Climate calculation","payload":{"title":"Climate calculation","question":"Compare scenarios","datasets":["dataset:1"]},"provenance":{"source_record_ids":["evidence:1"]}})


def test_registry_has_bidirectional_product_routes(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path))
    routes=c.routes()
    assert len(routes)==12
    pairs={(r["source_platform"],r["target_platform"]) for r in routes}
    assert ("site-intelligence","workbench") in pairs and ("workbench","site-intelligence") in pairs
    assert ("site-intelligence","research-lab") in pairs and ("research-lab","site-intelligence") in pairs


def test_packet_validation_and_digest(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path)); row=packet(c)
    assert row["status"]=="validated" and len(row["sha256"])==64
    assert c.validate_packet(row["packet_id"])["valid"] is True
    bad=c.create_packet({"route_id":"site-intelligence-to-workbench-analysis","payload":{"title":"Missing fields"}})
    assert bad["status"]=="draft" and c.validate_packet(bad["packet_id"])["valid"] is False


def test_queue_does_not_claim_remote_delivery(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path)); row=packet(c)
    queued=c.queue_packet(row["packet_id"])
    assert queued["attempt"]["remote_write_performed"] is False
    assert c.dispatch_preview(row["packet_id"])["external_delivery_enabled"] is False


def test_failed_receipt_and_human_confirmed_retry(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path)); row=packet(c); c.queue_packet(row["packet_id"])
    receipt=c.record_receipt(row["packet_id"],{"status":"failed","platform":"workbench","message":"Target unavailable"})
    assert receipt["status"]=="failed" and c.retry_preview(row["packet_id"])["automatic_retry"] is False
    with pytest.raises(ValueError,match="confirm=true"): c.retry_failed(row["packet_id"],{})
    assert c.retry_failed(row["packet_id"],{"confirm":True})["attempt"]["attempt_number"]==2


def test_linkbacks_and_export_are_audit_only(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path)); row=packet(c)
    link=c.add_linkback(row["packet_id"],{"platform":"workbench","record_id":"calculation:1"})
    assert link["verified"] is False
    body=c.export_packet(row["packet_id"])
    assert b"not proof of external ingestion" in body and b'"sha256"' in body


def test_incoming_typed_packet_returns_receipt(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path))
    result=c.ingest_incoming({"route_id":"workbench-to-site-intelligence-evidence","payload":{"title":"Calculated evidence","method":"symbolic","results":[{"value":2}]},"provenance":{"source_record_ids":["run:1"]}})
    assert result["ok"] is True and result["receipt"]["status"]=="accepted"


def test_public_boundary_exposes_routes_not_packets(tmp_path):
    c=CrossPlatformWorkflowCenter(settings(tmp_path)); packet(c)
    public=c.public_summary()
    assert public["governance"]["public_packet_payloads"] is False
    assert "packets" not in public and public["routes"]
    assert c.diagnostics(public=True)["summary"]=={"route_count":12,"platform_count":7}


def test_public_and_admin_api_contracts(tmp_path):
    current=settings(tmp_path); app.dependency_overrides[get_settings]=lambda:current
    try:
        client=TestClient(app)
        public=client.get("/public/cross-platform-workflows")
        assert public.status_code==200 and public.json()["version"]=="3.7.1"
        create=client.post("/admin/cross-platform-workflows/packets",json={"route_id":"site-intelligence-to-research-librarian-question","payload":{"question":"What evidence is missing?","scope":"climate"},"provenance":{"source_record_ids":["claim:1"]}})
        assert create.status_code==200
        packet_id=create.json()["packet_id"]
        assert client.get(f"/admin/cross-platform-workflows/packets/{packet_id}/validate").json()["valid"] is True
        assert client.get("/admin/cross-platform-workflows/control-center").json()["schema"]==SCHEMA_VERSION
    finally:
        app.dependency_overrides.clear()
