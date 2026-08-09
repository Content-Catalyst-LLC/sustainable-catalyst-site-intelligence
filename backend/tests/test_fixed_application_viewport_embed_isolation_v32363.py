from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_embed_isolation_contract():
    payload = CLIENT.get("/public/embed-isolation").json()
    assert payload["ok"] is True
    assert payload["version"] == "4.5.0"
    assert payload["application_embed"]["document_auto_resize"] is False
    assert payload["application_embed"]["internal_scrolling"] is True
    assert payload["message_policy"]["child_height_messages_enabled"] is False
    assert payload["message_policy"]["additive_height_adjustment_px"] == 0


def test_complete_application_shortcode_is_fixed_and_release_attribute_is_correct():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    for token in (
        "data-scsi-fixed-app",
        'data-scsi-embed-mode="fixed"',
        'data-scsi-release="%5$s"',
        'scrolling="yes"',
        "esc_attr(self::VERSION)",
    ):
        assert token in php
    block = php[php.index("public function standalone_app_shortcode"):php.index("public function geospatial_map_shortcode")]
    assert "wp_json_encode($frame_id)" not in block


def test_wordpress_host_ignores_height_messages_for_fixed_application():
    js = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
    for token in (
        "record.fixed",
        "if (!record.fixed) applyHeight",
        "if (record.fixed) return",
        "enforceFixedViewport",
        "Math.min(1400",
        "syncSiteIntelligencePublicRelease",
    ):
        assert token in js
    assert "parsed + 8" not in js


def test_fixed_application_css_disables_visibility_and_height_animation():
    css = read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
    block = css[css.rfind("v4.5.0"):]
    for token in (
        "content-visibility:visible!important",
        "contain:none!important",
        "transition:none!important",
        "--scsi-fixed-app-height",
    ):
        assert token in block


def test_child_application_disables_height_reporting_in_wordpress_mode():
    index = read("backend/public_app/index.html")
    appjs = read("backend/public_app/assets/app.js")
    embed = read("backend/public_app/assets/embed-isolation-v32363.js")
    assert index.index("embed-isolation-v32363.js") < index.index("app.js")
    assert "SCSI_FIXED_WORDPRESS_EMBED" in embed
    assert "wordpress-fixed" in embed
    assert "if(FIXED_WORDPRESS_EMBED)return" in appjs
    assert "if(!FIXED_WORDPRESS_EMBED)" in appjs


def test_runtime_health_includes_embed_isolation():
    health = CLIENT.get("/public/runtime-health").json()
    assert health["ok"] is True
    assert health["version"] == "4.5.0"
    assert "/public/embed-isolation" in {row["path"] for row in health["endpoint_contracts"]}
    check = {row["id"]: row for row in health["checks"]}["fixed-wordpress-embed-isolation"]
    assert check["status"] == "pass"


def test_full_application_assets_do_not_run_in_wordpress_host():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    for handle in (
        "scsi-production-truth",
        "scsi-data-truth",
        "scsi-browser-reliability",
        "scsi-embed-isolation",
    ):
        assert f"wp_enqueue_script('{handle}'" not in php
