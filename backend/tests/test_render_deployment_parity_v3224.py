from pathlib import Path

from fastapi.testclient import TestClient

from app.build_info import public_build_info
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def test_render_blueprint_enforces_commit_deploy_and_health_check():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "autoDeployTrigger: commit" in blueprint
    assert "healthCheckPath: /health" in blueprint
    assert "buildCommand: python -m pip install -r backend/requirements.txt" in blueprint
    assert "startCommand: cd backend && python -m uvicorn app.main:app" in blueprint


def test_build_info_exposes_public_render_commit_metadata(monkeypatch):
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-test")
    monkeypatch.setenv("RENDER_SERVICE_NAME", "sustainable-catalyst-site-intelligence")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://example.onrender.com")
    monkeypatch.setenv("RENDER_GIT_REPO_SLUG", "Content-Catalyst-LLC/sustainable-catalyst-site-intelligence")
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef")
    data = public_build_info()
    assert data["backend_version"] == "4.35.3.1"
    assert data["git_commit"] == "0123456789abcdef"
    assert data["deployment"]["platform"] == "render"
    assert data["deployment"]["git_commit_short"] == "0123456789ab"
    assert data["deployment"]["auto_deploy_contract"] == "commit"
    assert data["deployment"]["health_check_path"] == "/health"


def test_public_deployment_status_endpoint_is_available():
    response = client.get("/public/deployment-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.35.3.1"
    assert payload["expected_wordpress_plugin_version"] == "4.35.3.1"
    assert payload["verification_endpoints"]["build_info"] == "/public/build-info"
    assert payload["deployment"]["release_version"] == "4.35.3.1"


def test_promotion_script_pushes_before_render_verification():
    script = (ROOT / "promote_site_intelligence_v3_22_9_to_github_and_render_macos.sh").read_text(encoding="utf-8")
    assert "git push --atomic" in script
    assert "SC_SI_RENDER_DEPLOY_HOOK" in script
    assert "render deploys create" in script
    assert "/public/release-gate?plugin_version=" in script
    assert "expected_release_id=${RELEASE_ID}" in script
    assert "resuming Render verification" in script
    assert script.index("git push --atomic") < script.index("Verifying the live Render deployment receipt and release gate")
