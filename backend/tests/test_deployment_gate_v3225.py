from pathlib import Path

from fastapi.testclient import TestClient

from app.deployment_gate_v3225 import build_release_gate
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_release_gate_allows_matching_local_validation(monkeypatch):
    for name in ("RENDER_SERVICE_ID", "RENDER_EXTERNAL_URL", "RENDER_GIT_COMMIT", "RENDER_GIT_BRANCH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SC_SI_RELEASE_CHANNEL", "production")
    data = build_release_gate(plugin_version="4.35.10")
    assert data["backend_version"] == "4.35.10"
    assert data["install_allowed"] is True
    assert data["gate_state"] == "local-validation"
    assert data["checks"]["plugin_compatible"] is True
    assert len(data["release_fingerprint"]) == 20


def test_release_gate_blocks_plugin_mismatch():
    data = build_release_gate(plugin_version="3.22.4")
    assert data["install_allowed"] is False
    assert data["gate_state"] == "blocked"
    assert data["checks"]["plugin_compatible"] is False
    assert any("does not match" in reason for reason in data["reasons"])


def test_release_gate_verifies_render_branch_and_commit(monkeypatch):
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-test")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://example.onrender.com")
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef")
    monkeypatch.setenv("SC_SI_EXPECTED_GIT_BRANCH", "main")
    monkeypatch.setenv("SC_SI_RELEASE_CHANNEL", "production")
    data = build_release_gate(plugin_version="4.35.10", expected_commit="0123456789ab")
    assert data["install_allowed"] is True
    assert data["gate_state"] == "ready"
    assert data["checks"]["branch_verified"] is True
    assert data["checks"]["commit_verified"] is True


def test_release_gate_endpoint_is_uncacheable_and_public():
    response = client.get("/public/release-gate", params={"plugin_version": "4.35.10"})
    assert response.status_code == 200
    assert response.json()["version"] == "4.35.10"
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["x-sc-release-gate"] == "v4.35.10"


def test_render_blueprint_declares_release_contract():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "SC_SI_RELEASE_CHANNEL" in blueprint
    assert "SC_SI_EXPECTED_GIT_BRANCH" in blueprint
    assert "autoDeployTrigger: commit" in blueprint


def test_promotion_script_preserves_rollback_and_checks_gate():
    script = (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").read_text(encoding="utf-8")
    assert "ROLLBACK_TAG=" in script
    assert "PREVIOUS_COMMIT=" in script
    assert "git push --atomic" in script
    assert "/public/release-gate?plugin_version=" in script
    assert "expected_release_id=${RELEASE_ID}" in script
    assert "write_receipt" in script
    assert script.index("git push --atomic") < script.index("Verifying the live Render deployment receipt and release gate")


def test_wordpress_plugin_uses_release_gate_and_short_cache():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 4.35.10" in php
    assert "const RELEASE_GATE_MATCH_TTL = 900;" in php
    assert "$backend . '/public/release-gate'" in php
    assert "release_fingerprint" in php
    assert "Render commit" in php
