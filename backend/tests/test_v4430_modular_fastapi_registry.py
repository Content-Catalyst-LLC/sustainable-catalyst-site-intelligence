from __future__ import annotations

from collections import Counter

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.route_registry_v4430 import capability_manifest, route_inventory
from app.version import APP_VERSION, RELEASE_NAME

client = TestClient(app)


def test_v4430_release_identity() -> None:
    assert APP_VERSION == "4.43.0"
    assert RELEASE_NAME == "Modular FastAPI Route & Capability Registry"


def test_foundational_routes_are_physically_modularized() -> None:
    by_path = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
    expected = {
        "/health": "routers.system",
        "/public/build-info": "routers.system",
        "/public/data-truth": "routers.data_truth",
        "/public/record-truth/manifest": "routers.data_truth",
        "/public/capabilities": "routers.capabilities",
        "/public/routes/registry": "routers.capabilities",
    }
    for path, module_fragment in expected.items():
        assert path in by_path, path
        assert module_fragment in by_path[path].endpoint.__module__, (path, by_path[path].endpoint.__module__)


def test_capability_registry_inventories_complete_route_surface() -> None:
    manifest = capability_manifest(app.routes)
    assert manifest["version"] == APP_VERSION
    assert manifest["registry_version"] == "1.0.0"
    assert manifest["capability_count"] >= 14
    assert manifest["route_count"] > 1000
    assert manifest["modularized_route_count"] >= 30
    assert manifest["legacy_main_route_count"] > 0


def test_route_registry_has_no_duplicate_method_path_contracts() -> None:
    pairs = []
    for item in route_inventory(app.routes):
        for method in item["methods"]:
            pairs.append((method, item["path"]))
    counts = Counter(pairs)
    duplicates = {pair: count for pair, count in counts.items() if count > 1}
    assert duplicates == {}


def test_public_capability_endpoints_are_queryable() -> None:
    response = client.get("/public/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == APP_VERSION
    assert payload["route_count"] > 1000

    detail = client.get("/public/capabilities/data-truth")
    assert detail.status_code == 200
    assert detail.json()["route_count"] >= 20

    routes = client.get("/public/routes/registry", params={"capability": "data-truth", "modularized": "true"})
    assert routes.status_code == 200
    records = routes.json()["routes"]
    assert records
    assert all(item["capability_id"] == "data-truth" for item in records)
    assert all(item["modularized"] is True for item in records)


def test_existing_route_contracts_remain_available() -> None:
    for path in (
        "/health",
        "/public/build-info",
        "/public/release-gate",
        "/public/data-truth",
        "/public/workspace-evidence",
        "/public/record-truth/manifest",
        "/v1/energy-runtime/consumer",
        "/v1/energy-spatial/framework",
    ):
        assert any(isinstance(route, APIRoute) and route.path == path for route in app.routes), path
