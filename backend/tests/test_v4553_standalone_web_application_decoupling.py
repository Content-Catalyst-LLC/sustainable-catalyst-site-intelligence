from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.standalone_web_application_v4553 import (
    manifest, route_manifest, config_manifest, context_contract,
    wordpress_decoupling_contract, compatibility_manifest,
)

client=TestClient(app)
ROOT=Path(__file__).resolve().parents[2]


def test_release_identity_and_inventory():
    assert APP_VERSION=="4.55.3.2"
    assert RELEASE_NAME=="Standalone Functional Parity Recovery"
    m=capability_manifest(app.routes)
    assert m["registry_version"]=="2.6.0"
    assert m["route_count"]==1518
    assert m["modularized_route_count"]==209
    assert m["capability_count"]==31
    assert m["unclassified_route_count"]==0
    family=next(x for x in m["capabilities"] if x["capability_id"]=="standalone-web-application")
    assert family["route_count"]==6 and family["modularized_route_count"]==6
    keys=[(method,row["path"]) for row in route_inventory(app.routes) for method in row["methods"]]
    assert len(keys)==len(set(keys))


def test_web_manifest_separates_app_and_api_origins():
    m=manifest()
    assert m["application_origin"]=="https://intelligence.sustainablecatalyst.com"
    assert m["api_origin"]=="https://site-intelligence-api.sustainablecatalyst.com"
    assert m["application_origin"]!=m["api_origin"]
    assert m["wordpress_runtime_dependency"] is False
    assert m["wordpress_role"]=="public-site-launch-bridge"


def test_deep_link_route_contract():
    r=route_manifest()
    patterns={x["pattern"] for x in r["routes"]}
    for required in ["/country/:country","/dossiers/:country","/economics/:country","/law/:country","/science/:country","/science/earth/:country","/science/ocean","/science/space","/humanitarian/:country","/resources/:country","/events","/research","/packages/:package_id?"]:
        assert required in patterns
    assert r["routing_authority"]=="standalone-web-application"
    assert r["query_string_view_routing_authoritative"] is False


def test_context_is_real_application_state_not_decoration():
    c=context_contract()
    assert c["default_country_code"]=="KEN"
    assert c["country_context_is_decorative"] is False
    assert c["country_context_drives_workspace_requests"] is True
    for route in ["economics","law","science","humanitarian","resources","dossiers"]:
        assert route in c["propagates_to"]


def test_wordpress_is_not_runtime_authority():
    w=wordpress_decoupling_contract()
    assert w["wordpress_role"]=="public-site-launch-bridge"
    for key in ["standalone_boot_requires_wordpress","standalone_routing_requires_wordpress","standalone_state_requires_wordpress","standalone_api_transport_requires_wordpress","wordpress_is_application_authority","wordpress_is_state_authority","wordpress_is_api_proxy_authority"]:
        assert w[key] is False


def test_config_requires_explicit_cors_origin_without_wildcard():
    c=config_manifest()
    assert c["cors"]["required_origin"]=="https://intelligence.sustainablecatalyst.com"
    assert c["cors"]["wildcard_required"] is False
    assert c["api_transport"]["client_supplied_backend_urls_allowed"] is False


def test_http_surface_all_six_contract_routes():
    for path in ["/public/web-app/manifest","/public/web-app/routes","/public/web-app/config","/public/web-app/context","/public/web-app/wordpress-decoupling","/public/web-app/compatibility"]:
        res=client.get(path)
        assert res.status_code==200,path
        assert res.json()["ok"] is True


def test_standalone_web_artifact_has_no_wordpress_runtime_dependency():
    html=(ROOT/"web/index.html").read_text()
    appjs=(ROOT/"web/assets/app.js").read_text()
    api=(ROOT/"web/assets/api-client.js").read_text()
    router=(ROOT/"web/assets/router.js").read_text()
    assert "wordpress" not in appjs.lower()
    assert "site-intelligence-api.sustainablecatalyst.com" not in html
    assert "credentials" in api
    assert "/economics/" in router and "/law/" in router and "/humanitarian/" in router
    assert "/app/?view=" not in html+appjs+router


def test_spa_server_supports_history_fallback_and_health():
    nginx=(ROOT/"web/nginx.conf").read_text()
    compose=(ROOT/"web/compose.yml").read_text()
    dockerfile=(ROOT/"web/Dockerfile").read_text()
    assert "try_files $uri $uri/ /index.html" in nginx
    assert "location = /healthz" in nginx
    assert "127.0.0.1:8096:80" in compose
    assert "HEALTHCHECK" in dockerfile


def test_country_selection_drives_domain_paths_and_requests():
    router=(ROOT/"web/assets/router.js").read_text()
    views=(ROOT/"web/assets/views.js").read_text()
    assert 'economics:`/economics/${c}`' in router
    assert 'law:`/law/${c}`' in router
    assert 'geography_code:ctx.countryCode' in views
    assert 'country:ctx.countryCode' in views


def test_wordpress_plugin_is_launcher_not_application_host():
    php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3.2" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
    assert "const STANDALONE_WEB_APP_URL = 'https://intelligence.sustainablecatalyst.com';" in php
    block=php[php.index('public function standalone_app_shortcode'):php.index('public function geospatial_map_shortcode')]
    assert "<iframe" not in block
    assert "Site Intelligence now runs independently of WordPress" in block


def test_legacy_fastapi_app_remains_compatibility_only():
    c=compatibility_manifest()
    assert c["legacy_app_path_deprecated"] is True
    assert c["legacy_app_path_removed"] is False
    assert c["standalone_web_is_preferred"] is True
    old=(ROOT/"backend/app/standalone_authority_v4440.py").read_text()
    assert "legacy_fastapi_app_compatibility" in old
    assert "canonical_web_app_url" in old


def test_runtime_settings_always_allow_first_party_web_origin():
    from app.config import Settings
    settings=Settings(cors_origins="https://sustainablecatalyst.com", web_app_url="https://intelligence.sustainablecatalyst.com")
    assert "https://intelligence.sustainablecatalyst.com" in settings.cors_origin_list
    assert "*" not in settings.cors_origin_list
