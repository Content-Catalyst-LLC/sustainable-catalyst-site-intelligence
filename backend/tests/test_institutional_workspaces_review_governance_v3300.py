from fastapi.testclient import TestClient
from app.main import app

CLIENT=TestClient(app)

def payload():
    return {
        "workspace_id":"workspace:bra-review", "title":"Brazil evidence review", "summary":"Human review workspace.",
        "geographies":["BRA"], "prepared_by_role":"preparer",
        "evidence":[{"evidence_id":"bra-pop","title":"Brazil population","source_id":"world-bank","truth_state":"historical_only","review_state":"pending"}],
        "annotations":[{"annotation_id":"note:1","target_id":"bra-pop","annotation_type":"methodology","author_role":"reviewer","text":"Verify period and limitations."}],
    }

def test_governance_schema_has_bounded_institutional_contract():
    p=CLIENT.get("/public/institutional-governance").json()
    assert p["version"]=="4.35.15" and p["contract"]=="institutional-workspaces-review-governance"
    assert p["public_accounts_required"] is False and p["paid_multi_tenant_infrastructure_required"] is False
    assert p["automatic_evidence_approval"] is False and p["automatic_publication"] is False and p["public_write_performed"] is False

def test_portable_workspace_preview_is_stable_and_review_gated():
    a=CLIENT.post("/public/institutional-governance/workspace/preview",json=payload()).json()["workspace"]
    b=CLIENT.post("/public/institutional-governance/workspace/preview",json=payload()).json()["workspace"]
    assert a["workspace_sha256"]==b["workspace_sha256"] and len(a["workspace_sha256"])==64
    assert a["review_required"] and a["approval_required"] and a["write_performed"] is False

def test_review_queue_keeps_publisher_approval_separate():
    q=CLIENT.post("/public/institutional-governance/review-queue",json=payload()).json()
    assert q["count"]==1 and q["queue"][0]["required_role"]=="reviewer" and q["queue"][0]["publisher_approval_separate"] is True

def test_annotation_preview_is_structured_and_nonpersistent():
    a=CLIENT.post("/public/institutional-governance/annotation/preview",json={"target_id":"bra-pop","annotation_type":"concern","author_role":"reviewer","text":"Check denominator."}).json()["annotation"]
    assert a["annotation_type"]=="concern" and len(a["annotation_sha256"])==64

def test_preparer_cannot_self_approve_evidence():
    d=CLIENT.post("/public/institutional-governance/decision/preview",json={"workspace_id":"w","target_id":"e","actor_role":"preparer","prepared_by_role":"preparer","action":"approve_evidence"}).json()["decision"]
    assert d["allowed"] is False and d["decision_state"]=="blocked" and "role" in " ".join(d["reasons"]).lower()

def test_reviewer_can_prepare_evidence_approval_but_not_publication():
    d=CLIENT.post("/public/institutional-governance/decision/preview",json={"workspace_id":"w","target_id":"e","actor_role":"reviewer","prepared_by_role":"preparer","action":"approve_evidence"}).json()["decision"]
    assert d["allowed"] is True and d["human_confirmation_required"] is True and d["automatic_transition"] is False
    p=CLIENT.post("/public/institutional-governance/decision/preview",json={"workspace_id":"w","target_id":"w","actor_role":"reviewer","prepared_by_role":"preparer","action":"approve_publication"}).json()["decision"]
    assert p["allowed"] is False and p["required_role"]=="publisher"

def test_audit_preview_is_hash_chained_but_not_complete_history_claim():
    a=CLIENT.post("/public/institutional-governance/audit/preview",json=payload()).json()
    assert a["event_count"]==2 and len(a["chain_head_sha256"])==64 and a["complete_historical_log_claimed"] is False
    assert a["events"][1]["previous_event_sha256"]==a["events"][0]["event_sha256"]

def test_portable_export_import_preview_round_trip_without_write():
    ex=CLIENT.post("/public/institutional-governance/package/export",json=payload()).json()["package"]
    assert len(ex["package_sha256"])==64 and ex["remote_delivery_performed"] is False and ex["write_performed"] is False
    im=CLIENT.post("/public/institutional-governance/package/import-preview",json={"package":ex}).json()
    assert im["compatible"] is True and im["automatic_import"] is False and im["write_performed"] is False

def test_secret_fields_are_rejected():
    p=payload(); p["api_key"]="nope"
    assert CLIENT.post("/public/institutional-governance/workspace/preview",json=p).status_code==400

def test_assets_and_service_worker_ship_governance_layer():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    html=(root/"backend/public_app/index.html").read_text(); sw=(root/"backend/public_app/service-worker.js").read_text(); js=(root/"backend/public_app/assets/institutional-governance-v3300.js").read_text()
    assert "institutional-governance-v3300.js?v=4.35.15" in html and "institutional-governance-v3300.js" in sw and "SCSIInstitutionalGovernanceV3300" in js
