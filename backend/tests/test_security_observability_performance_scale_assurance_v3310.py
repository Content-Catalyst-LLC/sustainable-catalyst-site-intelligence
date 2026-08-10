from pathlib import Path
from fastapi.testclient import TestClient
from app.config import Settings, get_settings
from app.main import app

CLIENT=TestClient(app)

def test_production_assurance_public_contract():
    r=CLIENT.get("/public/production-assurance"); assert r.status_code==200
    d=r.json(); assert d["version"]=="4.28.0" and d["contract"]=="security-observability-performance-scale-assurance"
    assert d["summary"]["default_token_allowed"] is False and d["summary"]["persistent_visitor_profiles"] is False and len(d["assurance_sha256"])==64

def test_security_posture_is_fail_closed_and_privacy_safe():
    d=CLIENT.get("/public/production-assurance/security").json()
    assert d["production_fail_closed"] is True and d["default_development_token_rejected_in_production"] is True
    assert d["admin_rate_limit"]["key"]=="token-fingerprint" and d["admin_rate_limit"]["distributed"] is False
    assert d["cors"]["wildcard_origin"] is False

def test_production_default_token_is_rejected(tmp_path):
    current=Settings(environment="production",api_token="dev-token-change-me",production_database_path=str(tmp_path/"g.sqlite3"),production_backup_path=str(tmp_path/"b"))
    app.dependency_overrides[get_settings]=lambda:current
    try:
        c=TestClient(app); assert c.get("/admin/production-governance/control-center",headers={"X-SC-Intelligence-Token":"dev-token-change-me"}).status_code==401
    finally: app.dependency_overrides.clear()

def test_security_headers_and_server_timing_are_present():
    r=CLIENT.get("/app/"); assert r.status_code==200
    assert r.headers["x-content-type-options"]=="nosniff" and "app;dur=" in r.headers["server-timing"]
    csp=r.headers["content-security-policy"]; assert "default-src 'self'" in csp and "object-src 'none'" in csp and "frame-ancestors" in csp

def test_performance_budget_is_measured_against_shipped_assets():
    d=CLIENT.get("/public/production-assurance/performance").json(); assert d["ok"] is True
    assert d["observed"]["javascript_files"]>=40 and d["observed"]["largest_javascript_asset_bytes"]>0
    assert all(v["pass"] for v in d["checks"].values())

def test_rate_limit_preview_and_supply_chain_contracts():
    p=CLIENT.post("/public/production-assurance/rate-limit/preview",json={"requests":10,"window_seconds":60}).json(); assert p["preview"] is True and p["distributed_enforcement"] is False and p["write_performed"] is False
    s=CLIENT.get("/public/production-assurance/supply-chain").json(); assert s["hash_pinning_claimed"] is False and "pip check" in s["release_checks"]

def test_post_deploy_smoke_is_preview_only():
    d=CLIENT.post("/public/production-assurance/post-deploy/preview",json={"release":"4.28.0","commit":"abc123"}).json(); assert d["preview"]["network_requests_performed"] is False and d["preview"]["deployment_mutated"] is False and len(d["preview_sha256"])==64

def test_assets_and_service_worker_ship_v3310_layer():
    root=Path(__file__).resolve().parents[2]; html=(root/"backend/public_app/index.html").read_text(); sw=(root/"backend/public_app/service-worker.js").read_text(); js=(root/"backend/public_app/assets/security-performance-v3310.js").read_text()
    assert "security-performance-v3310.js?v=4.28.0" in html and "security-performance-v3310.js" in sw and "SCSIProductionAssuranceV3310" in js
