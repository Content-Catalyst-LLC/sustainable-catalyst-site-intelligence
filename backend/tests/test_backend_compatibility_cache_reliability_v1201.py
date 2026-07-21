from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "sustainable-catalyst-site-intelligence.php"


def test_backend_and_plugin_report_v1201():
    client = TestClient(app)
    root = client.get("/")
    build = client.get("/public/build-info")

    assert root.status_code == 200
    assert root.json()["version"] == "3.7.2"
    assert build.status_code == 200
    assert build.json()["backend_version"] == "3.7.2"
    assert build.json()["expected_wordpress_plugin_version"] == "3.7.2"


def test_wordpress_cache_reliability_contract():
    php = PLUGIN.read_text(encoding="utf-8")

    assert "Version: 3.7.2" in php
    assert "const VERSION = '3.7.2';" in php
    assert "BUILD_INFO_MATCH_TTL = 21600" in php
    assert "BUILD_INFO_MISMATCH_TTL = 45" in php
    assert "BUILD_INFO_ERROR_TTL = 30" in php
    assert "scsi_refresh_backend_version" in php
    assert "cache_bust" in php
    assert "plugin_version" in php
    assert "clear_all_build_info_cache" in php
    assert "register_activation_hook" in php
    assert "Refresh backend version" in php
    assert "invalid-response" in php
    assert "unavailable" in php
    assert "mismatch" in php
    assert "match" in php


def test_settings_save_and_upgrade_clear_cached_build_info():
    php = PLUGIN.read_text(encoding="utf-8")

    assert "maybe_upgrade" in php
    assert "INSTALLED_VERSION_OPTION" in php
    assert "clear_backend_build_info_cache((string) ($current['backend_url'] ?? ''))" in php
    assert "clear_backend_build_info_cache((string) ($output['backend_url'] ?? ''))" in php
    assert "delete_option(self::BUILD_INFO_STATUS_OPTION)" in php
