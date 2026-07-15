from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.experience_quality import (
    ACCESSIBILITY_TARGET,
    PERFORMANCE_BUDGETS,
    experience_checklist,
    experience_diagnostics,
    experience_profile,
)
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_experience_profile_declares_target_without_claiming_certification():
    payload = experience_profile()
    assert payload["application_version"] == "2.3.0"
    assert "target" in ACCESSIBILITY_TARGET.lower()
    assert "certification" in ACCESSIBILITY_TARGET.lower()
    assert payload["privacy"]["telemetry_added"] is False


def test_experience_checklist_keeps_manual_review_explicit():
    payload = experience_checklist()
    statuses = {item["id"]: item["status"] for item in payload["groups"]}
    assert statuses["keyboard-and-focus"] == "implemented"
    assert statuses["mobile-navigation"] == "implemented"
    assert statuses["manual-review"] == "review-required"
    assert payload["certification"] == "none"


def test_diagnostics_pass_and_first_party_files_fit_budgets():
    payload = experience_diagnostics()
    assert payload["ok"] is True
    assert all(payload["checks"].values())
    for key, limit in PERFORMANCE_BUDGETS.items():
        assert payload["file_sizes"][key] <= limit


def test_public_experience_endpoints():
    profile = client.get("/public/experience-profile")
    checklist = client.get("/public/experience-profile/checklist")
    diagnostics = client.get("/public/experience-profile/diagnostics")
    assert profile.status_code == checklist.status_code == diagnostics.status_code == 200
    assert profile.json()["application_version"] == "2.3.0"
    assert diagnostics.json()["ok"] is True


def test_delivery_headers_and_cache_policy():
    app_response = client.get("/app/")
    asset_response = client.get("/app/assets/app.css")
    profile_response = client.get("/public/experience-profile")
    for response in (app_response, asset_response, profile_response):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers["permissions-policy"]
    assert app_response.headers["cache-control"] == "no-cache"
    assert "stale-while-revalidate" in asset_response.headers["cache-control"]
    assert profile_response.headers["cache-control"] == "public, max-age=300"


def test_gzip_is_enabled_for_eligible_first_party_asset():
    response = client.get("/app/assets/app.js", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"
    assert "Accept-Encoding" in response.headers.get("vary", "")


def test_public_html_has_navigation_and_live_region_contracts():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert "viewport-fit=cover" in html
    assert 'id="mobileNavToggle"' in html
    assert 'aria-controls="siteNavigation"' in html
    assert 'id="mobileNavBackdrop"' in html
    assert 'id="routeAnnouncement"' in html
    assert 'id="primaryNavigation"' in html
    assert 'aria-current="page"' in html


def test_public_html_defers_scripts_and_does_not_eager_load_capture_library():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'src="/app/assets/app.js" defer' in html
    assert 'leaflet.js" defer' in html
    assert "html2canvas.min.js" not in html


def test_frontend_lazy_loads_png_capture_dependency():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert "function loadScriptOnce" in js
    assert "function ensureHtml2Canvas" in js
    assert "await ensureHtml2Canvas()" in js
    assert "cdn.jsdelivr.net/npm/html2canvas@1.4.1" in js


def test_frontend_mobile_navigation_updates_accessible_state():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert "function setMobileNavigation" in js
    assert 'setAttribute("aria-expanded",String(shouldOpen))' in js
    assert 'setAttribute("aria-current","page")' in js
    assert "main.inert=shouldOpen" in js
    assert 'e.key==="Escape"' in js


def test_frontend_respects_reduced_motion_for_playback():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert 'matchMedia?.("(prefers-reduced-motion: reduce)")' in js
    assert "Timeline autoplay is disabled by your reduced-motion preference." in js


def test_frontend_throttles_embed_height_messages():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    assert "let heightFrame=0" in js
    assert "requestAnimationFrame" in js
    assert "ResizeObserver" in js


def test_css_has_mobile_safe_area_touch_targets_and_route_drawer():
    css = (ROOT / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    assert "min-height:44px" in css or "min-height: 44px" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "100dvh" in css
    assert "body.mobile-nav-open .sidebar" in css
    assert "content-visibility:auto" in css or "content-visibility: auto" in css


def test_css_has_reduced_motion_and_forced_color_modes():
    css = (ROOT / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    assert "@media(prefers-reduced-motion:reduce)" in css
    assert "@media(forced-colors:active)" in css
    assert "animation-duration:.001ms" in css


def test_wordpress_embed_contract_is_lazy_and_origin_checked():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 2.3.0" in php
    assert "const VERSION = '2.3.0';" in php
    assert 'loading="lazy"' in php
    assert 'allow="fullscreen; clipboard-write"' in php
    assert "e.origin!==expectedOrigin" in php


def test_source_methodology_registry_documents_experience_delivery():
    from app.source_methodology_studio import methodology_directory

    payload = methodology_directory()
    ids = {item["id"] for item in payload["methods"]}
    assert "accessible-responsive-delivery" in ids


def test_application_version_is_aligned_across_frontend_and_backend():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    version = (ROOT / "backend/app/version.py").read_text(encoding="utf-8")
    assert 'APP_VERSION="2.3.0"' in js
    assert 'APP_VERSION = "2.3.0"' in version
