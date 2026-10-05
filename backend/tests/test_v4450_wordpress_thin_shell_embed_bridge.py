from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME
from app.wordpress_bridge_v4450 import (
    BRIDGE_CONTRACT_VERSION,
    CANONICAL_SHORTCODES,
    COMPATIBILITY_SHORTCODE_COUNT,
    WORDPRESS_ROLE,
)

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php"


def test_release_identity() -> None:
    assert APP_VERSION == "4.45.0"
    assert RELEASE_NAME == "WordPress Thin-Shell & Embed Bridge"
    assert BRIDGE_CONTRACT_VERSION == "1.0.0"
    assert WORDPRESS_ROLE == "thin-shell-and-embed-bridge"


def test_bridge_contract_makes_fastapi_authoritative() -> None:
    payload = client.get("/public/integrations/wordpress/bridge").json()
    assert payload["ok"] is True
    assert payload["version"] == APP_VERSION
    assert payload["wordpress_role"] == WORDPRESS_ROLE
    assert payload["product_authority"] == "fastapi"
    assert payload["canonical_application"] == "/app/"
    assert payload["runtime_mode"] == "wordpress-embed"
    assert payload["boundaries"]["wordpress_feature_authority"] is False
    assert payload["boundaries"]["wordpress_new_feature_shortcodes"] is False
    assert payload["boundaries"]["legacy_shortcode_compatibility"] is True


def test_embed_contract_is_explicit_and_credential_free() -> None:
    payload = client.get("/public/integrations/wordpress/embed-contract").json()
    assert payload["mode"] == "iframe"
    assert payload["surface"] == "wordpress-embed"
    assert payload["query_transport"]["release"] == APP_VERSION
    assert payload["query_transport"]["bridge"] == "wordpress"
    assert payload["security"]["credentials_in_query"] is False
    assert payload["messaging"]["origin_validation_required"] is True
    assert "scsi-wordpress-bridge-ready" in payload["messaging"]["app_to_parent"]


def test_auth_handoff_does_not_claim_global_auth() -> None:
    payload = client.get("/public/integrations/wordpress/auth-handoff").json()
    assert payload["mode"] == "optional-delegated-handoff"
    assert payload["status"] == "contract-ready-no-global-session-authority"
    assert payload["fastapi_session_authority"] is False
    assert payload["wordpress_session_authority"] is False
    assert payload["token_transport"] == "not-enabled"


def test_compatibility_contract_preserves_published_shortcodes() -> None:
    payload = client.get("/public/integrations/wordpress/compatibility").json()
    assert payload["retained_shortcode_count"] == 72 == COMPATIBILITY_SHORTCODE_COUNT
    assert tuple(payload["canonical_bridge_shortcodes"]) == CANONICAL_SHORTCODES
    assert payload["policy"]["existing_published_shortcodes"] == "preserved"
    assert payload["policy"]["new_feature_shortcodes"] == "prohibited"
    assert payload["policy"]["new_product_features"] == "standalone-fastapi-first"


def test_capability_registry_has_dedicated_wordpress_family() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["version"] == APP_VERSION
    assert manifest["registry_version"] == "1.2.0"
    assert manifest["route_count"] == 1361
    assert manifest["modularized_route_count"] == 52
    assert manifest["capability_count"] == 16
    assert manifest["unclassified_route_count"] == 0
    wp = next(item for item in manifest["capabilities"] if item["capability_id"] == "wordpress-integration")
    assert wp["route_count"] == 4
    assert wp["modularized_route_count"] == 4


def test_standalone_bootstrap_declares_thin_shell_role() -> None:
    payload = client.get("/public/app/bootstrap", params={"surface": "wordpress-embed"}).json()
    assert payload["authority"]["backend"] == "fastapi"
    assert payload["authority"]["canonical"] is True
    assert payload["authority"]["wordpress_role"] == WORDPRESS_ROLE
    assert payload["runtime"]["mode"] == "wordpress-embed"
    assert payload["contract_version"] == "1.1.0"


def test_wordpress_plugin_exposes_only_bridge_facing_new_routes() -> None:
    php = PLUGIN.read_text(encoding="utf-8")
    assert "const BRIDGE_CONTRACT_VERSION = '1.0.0';" in php
    assert "const WORDPRESS_ROLE = 'thin-shell-and-embed-bridge';" in php
    for route in ("/bridge", "/bridge/bootstrap", "/bridge/navigation", "/bridge/embed-contract", "/bridge/auth-handoff", "/bridge/compatibility"):
        assert f"'{route}'" in php
    assert "$query['surface'] = 'wordpress-embed';" in php
    assert "$query['bridge'] = 'wordpress';" in php
    assert "$query['bridge_version'] = self::BRIDGE_CONTRACT_VERSION;" in php


def test_protected_generic_embed_no_longer_relies_on_this() -> None:
    php = PLUGIN.read_text(encoding="utf-8")
    start = php.index("function scsi_site_intelligence_embed_shortcode_v2110")
    end = php.index("add_shortcode('sc_site_intelligence_embed'", start)
    block = php[start:end]
    assert "$this->app_embed_url" not in block
    assert "thin-shell-and-embed-bridge" in block
    assert "SC_Site_Intelligence_Plugin::BRIDGE_CONTRACT_VERSION" in block
    assert "SC_Site_Intelligence_Plugin::options()" in block


def test_browser_bridge_messages_are_versioned_and_origin_checked() -> None:
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    wp_js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text(encoding="utf-8")
    assert 'type:"scsi-wordpress-bridge-ready"' in app_js
    assert 'bridgeVersion:"1.0.0"' in app_js
    assert "scsi-wordpress-bridge-ready" in wp_js
    assert "event.origin !== record.origin" in wp_js
    assert "bridge_version','1.0.0'" in wp_js


def test_route_contract_remains_duplicate_free() -> None:
    pairs = []
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method, item["path"]))
    assert {pair: count for pair, count in Counter(pairs).items() if count > 1} == {}
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    for path in (
        "/health",
        "/public/build-info",
        "/public/release-gate",
        "/public/app/bootstrap",
        "/public/integrations/wordpress/bridge",
        "/public/integrations/wordpress/embed-contract",
        "/public/integrations/wordpress/auth-handoff",
        "/public/integrations/wordpress/compatibility",
        "/public/data-truth",
        "/v1/energy-runtime/consumer",
        "/v1/energy-spatial/framework",
    ):
        assert path in paths
