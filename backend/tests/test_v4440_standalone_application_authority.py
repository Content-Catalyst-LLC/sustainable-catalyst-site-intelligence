from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.standalone_authority_v4440 import CACHE_GENERATION, navigation_model
from app.version import APP_VERSION, RELEASE_NAME

client = TestClient(app)


def test_v4440_release_identity() -> None:
    assert APP_VERSION == "4.44.0"
    assert RELEASE_NAME == "Standalone Site Intelligence Application Authority"
    assert CACHE_GENERATION == "scsi-v4.44.0"


def test_standalone_routes_are_modular_and_canonical() -> None:
    by_path = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
    for path in (
        "/public/app/bootstrap",
        "/public/app/runtime-handshake",
        "/public/app/navigation",
        "/public/app/session-contract",
        "/app/manifest.webmanifest",
        "/app/service-worker.js",
        "/app/offline.html",
        "/app/{route:path}",
    ):
        assert path in by_path, path
        assert "routers.standalone" in by_path[path].endpoint.__module__


def test_bootstrap_declares_fastapi_as_authority() -> None:
    response = client.get("/public/app/bootstrap")
    assert response.status_code == 200
    assert response.headers["x-sc-application-authority"] == "fastapi"
    assert response.headers["x-sc-canonical-app"] == "/app/"
    payload = response.json()
    assert payload["version"] == APP_VERSION
    assert payload["authority"]["backend"] == "fastapi"
    assert payload["authority"]["frontend"] == "standalone-web-app"
    assert payload["authority"]["canonical_app_path"] == "/app/"
    assert payload["authority"]["canonical"] is True
    assert payload["authority"]["wordpress_role"] == "optional-integration-and-publication-surface"
    assert payload["runtime"]["mode"] == "standalone-authoritative"
    assert payload["runtime"]["deep_links"] is True
    assert payload["runtime"]["offline_shell"] is True
    assert payload["capability_registry"]["unclassified_route_count"] == 0


def test_wordpress_embed_mode_is_explicit_but_not_authoritative() -> None:
    payload = client.get("/public/app/bootstrap", params={"surface": "wordpress-embed"}).json()
    assert payload["runtime"]["mode"] == "wordpress-embed"
    assert payload["authority"]["backend"] == "fastapi"
    assert payload["authority"]["canonical"] is True


def test_runtime_handshake_requires_exact_release_identity() -> None:
    good = client.get("/public/app/runtime-handshake", params={"client_version": APP_VERSION}).json()
    assert good["ok"] is True
    assert good["compatible"] is True
    assert good["action"] == "continue"
    bad = client.get("/public/app/runtime-handshake", params={"client_version": "4.43.0"}).json()
    assert bad["ok"] is False
    assert bad["compatible"] is False
    assert bad["action"] == "reload"


def test_navigation_is_capability_registry_driven() -> None:
    payload = client.get("/public/app/navigation").json()
    assert payload["source"] == "/public/capabilities"
    assert payload["registry_version"] == "1.1.0"
    assert len(payload["items"]) >= 30
    assert all(item["capability_id"] for item in payload["items"])
    assert all(item["available"] is True for item in payload["items"])
    assert {"overview", "earth", "country", "events", "sources", "saved"}.issubset({item["route"] for item in payload["items"]})


def test_browser_local_session_contract_is_explicit() -> None:
    payload = client.get("/public/app/session-contract").json()
    assert payload["authority"] == "browser-local"
    assert payload["authentication_required"] is False
    assert payload["server_profile_required"] is False
    assert payload["persistence"]["saved_views"] == "localStorage"
    assert payload["persistence"]["workspace_state"] == "URLSearchParams"
    assert payload["persistence"]["offline_shell"] == "CacheStorage"
    assert payload["persistence"]["server_mutation"] is False


def test_deep_links_and_pwa_assets_are_served() -> None:
    for path in ("/app/", "/app/country/KEN", "/app/manifest.webmanifest", "/app/service-worker.js", "/app/offline.html"):
        response = client.get(path)
        assert response.status_code == 200, path
    assert "4.44.0" in client.get("/app/manifest.webmanifest").text
    assert "4.44.0" in client.get("/app/service-worker.js").text


def test_frontend_bootstraps_from_fastapi_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    index = (root / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'STANDALONE_BOOTSTRAP_ENDPOINT="/public/app/bootstrap"' in app_js
    assert 'STANDALONE_HANDSHAKE_ENDPOINT="/public/app/runtime-handshake"' in app_js
    assert "establishStandaloneAuthority" in app_js
    assert "applyRegistryNavigation" in app_js
    assert 'data-scsi-release="4.44.0"' in index
    assert 'id="standaloneAuthorityBar"' in index


def test_registry_remains_complete_and_duplicate_free() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["version"] == APP_VERSION
    assert manifest["registry_version"] == "1.1.0"
    assert manifest["route_count"] > 1000
    assert manifest["modularized_route_count"] >= 45
    assert manifest["unclassified_route_count"] == 0
    pairs = []
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method, item["path"]))
    assert {pair: count for pair, count in Counter(pairs).items() if count > 1} == {}


def test_existing_major_route_contracts_are_preserved() -> None:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    for path in (
        "/health",
        "/public/build-info",
        "/public/release-gate",
        "/public/capabilities",
        "/public/routes/registry",
        "/public/data-truth",
        "/public/workspace-evidence",
        "/v1/energy-runtime/consumer",
        "/v1/energy-spatial/framework",
    ):
        assert path in paths
