from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.public_launch_portfolio import (
    DEPRECATED_SHORTCODES,
    PUBLIC_POSITIONING,
    PUBLIC_WORKSPACES,
    launch_checklist,
    launch_diagnostics,
    launch_materials,
    launch_profile,
    portfolio_manifest,
    portfolio_markdown,
)

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_launch_profile_is_public_release_and_version_aligned():
    payload = launch_profile()
    assert payload["application_version"] == "3.1.2"
    assert payload["release_status"] == "auditable-public-observatory"
    assert payload["positioning"] == PUBLIC_POSITIONING


def test_launch_profile_registers_all_public_research_workspaces():
    payload = launch_profile()
    assert len(payload["workspaces"]) == 20
    assert {item["id"] for item in payload["workspaces"]} == {item["id"] for item in PUBLIC_WORKSPACES}
    assert all(item["route"].startswith("/app/?view=") for item in payload["workspaces"])


def test_launch_calls_to_action_match_public_product_structure():
    calls = launch_profile()["calls_to_action"]
    assert calls["primary"] == {"label": "Open Site Intelligence", "route": "/app/?view=overview"}
    assert calls["secondary"]["route"] == "/app/?view=earth"
    assert calls["github"]["url"].startswith("https://github.com/Content-Catalyst-LLC/")


def test_launch_checklist_separates_automated_readiness_from_manual_launch_work():
    payload = launch_checklist()
    statuses = {group["id"]: group["status"] for group in payload["groups"]}
    assert payload["automated_ready"] is True
    assert statuses["manual-launch"] == "review-required"
    assert payload["manual_review_required"] is True


def test_launch_materials_include_portfolio_and_social_copy():
    payload = launch_materials()
    assert payload["homepage_feature"]["primary_cta"] == "Open Site Intelligence"
    assert "open-source public-interest observatory" in payload["linkedin_project_description"]
    assert payload["social_preview"]["recommended_size"] == "1200x630"
    assert len(payload["demo_shot_list"]) >= 7


def test_portfolio_manifest_preserves_architecture_and_responsible_use():
    payload = portfolio_manifest()
    assert payload["schema"] == "sc-site-intelligence-portfolio/1.0"
    assert "FastAPI" in payload["project"]["architecture"]
    assert "emergency response" in payload["responsible_use"]["not_for"]
    assert len(payload["workspaces"]) == 20


def test_portfolio_markdown_is_download_ready():
    body = portfolio_markdown()
    assert body.startswith("# Sustainable Catalyst Site Intelligence")
    assert "**Release:** v3.1.2" in body
    assert "## Public workspaces" in body
    assert "Repository:" in body


def test_public_launch_profile_endpoints():
    for path in ("/public/launch-profile", "/public/launch-profile/checklist", "/public/launch-profile/materials", "/public/launch-profile/diagnostics"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["application_version"] == "3.1.2"


def test_public_portfolio_endpoint_supports_json_and_markdown():
    json_response = client.get("/public/launch-profile/portfolio?format=json")
    markdown_response = client.get("/public/launch-profile/portfolio?format=markdown")
    invalid_response = client.get("/public/launch-profile/portfolio?format=pdf")
    assert json_response.status_code == 200
    assert json_response.json()["schema"] == "sc-site-intelligence-portfolio/1.0"
    assert markdown_response.status_code == 200
    assert markdown_response.headers["content-type"].startswith("text/markdown")
    assert invalid_response.status_code == 422


def test_launch_diagnostics_pass_without_exposing_secrets():
    payload = launch_diagnostics()
    assert payload["ok"] is True
    assert all(payload["checks"].values())
    assert payload["secrets_exposed"] is False
    assert payload["workspace_count"] == 20


def test_standalone_app_has_launch_route_portfolio_and_social_metadata():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'data-route="launch"' in html
    assert 'id="publicLaunchPortfolio"' in html
    assert "Public evidence becomes navigable research infrastructure" in html
    assert 'property="og:title"' in html
    assert 'name="twitter:card"' in html


def test_frontend_loads_launch_profile_and_handles_launch_route():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'APP_VERSION="3.1.2"' in js
    assert 'route==="launch"' in js
    assert "function openPublicLaunchPortfolio" in js
    assert 'apiWithRetry("/public/launch-profile"' in js
    assert '"saved","launch"' in js


def test_wordpress_launch_shortcode_and_deprecation_schedule():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 3.1.2" in php
    assert "const VERSION = '3.1.2';" in php
    assert "add_shortcode('sc_site_intelligence_launch'" in php
    assert "public function site_intelligence_launch_shortcode" in php
    assert "/app/?view=launch" in php
    assert "LEGACY_SHORTCODE_REMOVAL_TARGET = 'fulfilled-in-2.0.0'" in php
    assert len(DEPRECATED_SHORTCODES) == 3


def test_release_documentation_and_manifest_are_complete():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    manifest = (ROOT / "docs/RELEASE_MANIFEST_V1250.json").read_text(encoding="utf-8")
    assert "**Current release:** v3.1.2" in readme
    assert "## 1.25.0 — Public Launch and Portfolio Release" in changelog
    assert '"release": "1.25.0"' in manifest
    assert (ROOT / "docs/PUBLIC_LAUNCH_PORTFOLIO_V1250.md").exists()
    assert (ROOT / "docs/LAUNCH_MATERIALS_V1250.md").exists()
