from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.deployment_gate_v3226 import build_release_gate
from app.deployment_receipt_v3226 import public_deployment_receipt
from app.live_intelligence_reliability_v361 import LiveIntelligenceReliabilityStore
from app.live_intelligence_rotation_v371 import LiveIntelligenceRotationStore
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_runtime_receipt_has_release_identity(monkeypatch):
    monkeypatch.setenv("SC_SI_RELEASE_ID", "site-intelligence-v4.38.0")
    data = public_deployment_receipt()
    assert data["version"] == "4.38.0"
    assert data["release_id"] == "site-intelligence-v4.38.0"
    assert len(data["receipt_fingerprint"]) == 24


def test_release_gate_checks_expected_release_id(monkeypatch):
    monkeypatch.setenv("SC_SI_RELEASE_ID", "site-intelligence-v4.38.0")
    ready = build_release_gate(plugin_version="4.38.0", expected_release_id="site-intelligence-v4.38.0")
    blocked = build_release_gate(plugin_version="4.38.0", expected_release_id="wrong-release")
    assert ready["checks"]["release_id_verified"] is True
    assert blocked["checks"]["release_id_verified"] is False
    assert blocked["install_allowed"] is False


def test_deployment_receipt_endpoint_is_uncacheable():
    response = client.get("/public/deployment-receipt")
    assert response.status_code == 200
    assert response.json()["version"] == "4.38.0"
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"


def test_runtime_root_isolates_last_known_good(tmp_path):
    settings = Settings(runtime_state_root=str(tmp_path), live_intelligence_last_known_good_path="backend/data/example.json")
    store = LiveIntelligenceReliabilityStore(settings)
    assert store.path == tmp_path / "example.json"
    rotation = LiveIntelligenceRotationStore(Settings(runtime_state_root=str(tmp_path), live_intelligence_rotation_state_path="backend/data/rotation.json"))
    assert rotation.path == tmp_path / "rotation.json"


def test_render_blueprint_declares_release_and_runtime_identity():
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "SC_SI_RELEASE_ID" in text
    assert "site-intelligence-v4.38.0" in text
    assert "SC_SI_RUNTIME_STATE_ROOT" in text


def test_promotion_is_resume_safe_and_writes_receipt():
    text = (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").read_text(encoding="utf-8")
    assert "DEPLOYMENT_RECEIPT=" in text
    assert "write_receipt" in text
    assert "git push --atomic" in text
    assert "resuming Render verification" in text
    assert "REMOTE_NOW" in text
    assert "expected_release_id=${RELEASE_ID}" in text


def test_wordpress_requests_release_id_and_reads_receipt():
    text = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "const RELEASE_ID = 'site-intelligence-v4.38.0';" in text
    assert "'expected_release_id' => self::RELEASE_ID" in text
    assert "receipt_fingerprint" in text


def test_build_info_and_status_publish_release_id(monkeypatch):
    monkeypatch.setenv("SC_SI_RELEASE_ID", "site-intelligence-v4.38.0")
    build = client.get("/public/build-info").json()
    status = client.get("/public/deployment-status").json()
    assert build["release_id"] == "site-intelligence-v4.38.0"
    assert build["deployment"]["release_id"] == "site-intelligence-v4.38.0"
    assert status["release_id"] == "site-intelligence-v4.38.0"
    assert status["verification_endpoints"]["deployment_receipt"] == "/public/deployment-receipt"
