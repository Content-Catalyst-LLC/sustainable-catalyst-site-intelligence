from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
CLIENT = TestClient(app)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_map_interaction_contract_is_complete():
    response = CLIENT.get("/public/maps/interaction")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "4.33.0"
    assert payload["release_id"] == "site-intelligence-v4.33.0"
    assert payload["contract"] == "cartographic-interaction-and-layer-control"
    assert len(payload["base_styles"]) == 3
    assert len(payload["semantic_categories"]) == 7
    assert all(payload["layer_controls"].values())
    assert payload["interaction_contract"]["list_to_map_selection"] == "synchronized"
    assert "mapSelected" in payload["url_state"]


def test_app_shell_loads_interaction_after_workspace_and_before_truth():
    html = read("backend/public_app/index.html")
    assert '/app/assets/cartographic-interaction-v3232.css?v=4.33.0' in html
    assert '/app/assets/cartographic-interaction-v3232.js?v=4.33.0' in html
    assert html.index("app.js") < html.index("cartographic-workspace-v3230.js") < html.index("cartographic-interaction-v3232.js") < html.index("production-truth-v3231.js")


def test_overview_map_runtime_supports_filters_clusters_selection_and_url_state():
    app_js = read("backend/public_app/assets/app.js")
    for token in (
        "SCSIOverviewMapV3232",
        "semanticCategory",
        "clusterOverviewFeatures",
        "filteredOverviewFeatures",
        "renderOverviewFeatures",
        "selectOverviewEvent",
        "fitOverviewResults",
        "mapCategories",
        "mapSource",
        "mapDays",
        "mapCluster",
        "mapCenter",
        "mapZoom",
        "mapSelected",
        "markerIndex:new Map()",
        "data-event-id",
    ):
        assert token in app_js


def test_interaction_panel_has_layer_opacity_filters_and_semantic_legend():
    js = read("backend/public_app/assets/cartographic-interaction-v3232.js")
    css = read("backend/public_app/assets/cartographic-interaction-v3232.css")
    for token in (
        "mapInteractionPanel",
        "mapBaseStyle",
        "mapImageryOpacity",
        "mapCategoryFilter",
        "mapSourceFilter",
        "mapRecencyFilter",
        "mapClusterEvents",
        "mapFitResults",
        "mapShareState",
        "mapSemanticLegend",
        "SCSICartographicInteractionV3232",
    ):
        assert token in js
    for token in ("scsi-map-cluster", "semantic-earthquake", "semantic-wildfire", "map-filter-summary", 'data-map-style'):
        assert token in css


def test_runtime_health_and_offline_shell_require_interaction_assets():
    payload = CLIENT.get("/public/runtime-health").json()
    assert payload["ok"] is True
    paths = {item["path"] for item in payload["assets"]}
    assert "/app/assets/cartographic-interaction-v3232.js" in paths
    assert "/app/assets/cartographic-interaction-v3232.css" in paths
    endpoints = {item["path"] for item in payload["endpoint_contracts"]}
    assert "/public/maps/interaction" in endpoints
    worker = read("backend/public_app/service-worker.js")
    assert "cartographic-interaction-v3232.js" in worker
    assert "cartographic-interaction-v3232.css" in worker


def test_wordpress_packages_interaction_assets_but_keeps_app_runtime_out_of_host_document():
    php = read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.33.0" in php
    assert "mapInteractionCssUrl" in php and "mapInteractionJsUrl" in php
    assert "wp_enqueue_script('scsi-production-truth'" not in php
    assert "wp_enqueue_script('scsi-cartographic-interaction'" not in php
    for name in ("cartographic-interaction-v3232.js", "cartographic-interaction-v3232.css"):
        assert (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name).is_file()
