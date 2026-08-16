from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.ocean_observation_marine_systems_v4360 import SYSTEMS

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_ocean_observation_overview_composes_existing_marine_systems_without_new_public_route():
    payload = CLIENT.get("/public/ocean-observation").json()
    assert payload["ok"] is True
    assert payload["version"] == "4.36.0"
    assert payload["contract"] == "global-ocean-intelligence-ii-ocean-observation-marine-systems"
    assert payload["route"] == "earth" and payload["mode"] == "ocean"
    assert payload["system_count"] == 11 == len(SYSTEMS)
    assert payload["public_route_count_delta"] == 0
    assert payload["navigation"]["visible_primary_entry"] == "Ocean"
    assert payload["navigation"]["preserves_v4_route_contract"] is True
    assert payload["source_registration_count"] >= 40
    assert payload["unique_source_count"] >= 30
    assert len(payload["contract_sha256"]) == 64


def test_ocean_observation_catalog_spans_physical_living_operational_and_governance_domains():
    payload = CLIENT.get("/public/ocean-observation/catalog").json()
    assert payload["ok"] is True
    ids = {row["id"] for row in payload["systems"]}
    assert ids == {"surface", "water-column", "seafloor", "underwater", "biodiversity", "missions", "events", "human-activity", "pollution", "coastal-change", "governance"}
    assert {row["id"] for row in payload["groups"]} == {"physical-ocean", "observing-systems", "living-ocean", "ocean-change", "human-ocean"}
    assert all(row["source_count"] >= 3 for row in payload["systems"])
    assert any("NOAA" in row["title"] for row in payload["source_index"])
    assert len(payload["catalog_sha256"]) == 64


def test_ocean_readiness_is_network_free_and_inherits_all_eleven_systems():
    payload = CLIENT.get("/public/ocean-observation/readiness").json()
    assert payload["ok"] is True
    assert payload["network_calls_performed"] is False
    assert payload["upstream_health_release_blocking"] is False
    assert payload["inherited_route_count"] == 35
    assert payload["primary_area_count"] == 6
    assert payload["public_route_count_delta"] == 0
    assert len(payload["systems"]) == 11
    assert all(row["ok"] for row in payload["systems"].values())
    assert all(payload["checks"].values())


def test_ocean_workspace_manifest_preserves_truth_and_source_lineage():
    payload = CLIENT.get("/public/ocean-observation/manifest").json()
    assert payload["ok"] is True
    assert payload["schema"] == "sc-site-intelligence-ocean-observation-workspace/1.0"
    assert payload["review"]["new_public_route_created"] is False
    assert payload["review"]["ocean_navigation_is_first_class"] is True
    assert payload["review"]["existing_ocean_contracts_composed"] is True
    assert payload["review"]["network_calls_performed"] is False
    assert len(payload["systems"]) == 11
    assert len(payload["manifest_sha256"]) == 64
    assert any("Missing ocean data remains missing" in item for item in payload["truth_boundaries"])


def test_ocean_is_explicitly_visible_in_primary_navigation_and_launch_portfolio():
    index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'data-ocean-entry="hub" data-nav-group="analysis" data-nav-after-route="earth" data-nav-featured="true" data-route-alias="earth"><span>Ocean</span><small>Observation and marine systems</small>' in index
    assert "Open Ocean Intelligence" in index
    assert 'id="oceanObservationStudio"' in index
    assert 'data-scsi-ocean-contract="global-ocean-intelligence-ii-ocean-observation-marine-systems"' in index
    assert "/app/assets/ocean-observation-v4360.js?v=4.36.0" in index
    assert "/app/assets/ocean-observation-v4360.css?v=4.36.0" in index
    unified = (ROOT / "backend/public_app/assets/unified-platform-v4000.js").read_text(encoding="utf-8")
    assert '.nav-item[data-nav-group]:not([data-route])' in unified
    assert 'item.dataset.navAfterRoute===route' in unified
    assert 'item.dataset.navFeatured==="true"' in unified
    assert 'featuredWrap.className="v4000-nav-featured"' in unified
    cartographic = (ROOT / "backend/public_app/assets/cartographic-workspace-v3230.js").read_text(encoding="utf-8")
    assert ".nav-item.active[data-route-alias]" in cartographic
    assert 'pending.filter(item=>!item.isConnected)' in unified


def test_ocean_browser_controller_exposes_direct_access_to_every_inherited_marine_system():
    js = (ROOT / "backend/public_app/assets/ocean-observation-v4360.js").read_text(encoding="utf-8")
    for system in SYSTEMS:
        assert f'id:"{system["id"]}"' in js
        assert system["global"] in js
        assert system["asset"] in js
    assert "SCSIOceanObservationV4360" in js
    assert "oceanMode" in js and "oceanSystem" in js
    assert 'await Promise.resolve(window.SCSIRouterV3228?.navigate?.("earth"))' in js
    shell_gate = (ROOT / "scripts/browser_complete_shell_gate_v32362.py").read_text(encoding="utf-8")
    assert "'/public/ocean-observation/catalog'" in shell_gate
    assert "'/public/ocean-observation/readiness'" in shell_gate


def test_ocean_workspace_assets_are_mirrored_into_wordpress_plugin():
    for name in ("ocean-observation-v4360.js", "ocean-observation-v4360.css", "unified-platform-v4000.js", "unified-platform-v4000.css"):
        backend = ROOT / "backend/public_app/assets" / name
        wordpress = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name
        assert backend.read_bytes() == wordpress.read_bytes()


def test_ocean_workspace_is_in_critical_offline_shell():
    sw = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert '"/app/assets/ocean-observation-v4360.css"' in sw
    assert '"/app/assets/ocean-observation-v4360.js"' in sw


def test_public_launch_profile_has_a_direct_ocean_workspace_without_expanding_v4_route_registry():
    payload = CLIENT.get("/public/launch-profile").json()
    ocean = next(row for row in payload["workspaces"] if row["id"] == "ocean")
    assert ocean["route"] == "/app/?view=earth&oceanMode=hub"
    nav = CLIENT.get("/public/v4/navigation").json()
    assert nav["route_count"] == 35 and nav["primary_area_count"] == 6
    assert "ocean" not in {row["route_id"] for row in nav["routes"]}


def test_release_identity_is_v4360_across_backend_app_and_wordpress_plugin():
    assert CLIENT.get("/public/build-info").json()["version"] == "4.36.0"
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'const APP_VERSION="4.36.0"' in app_js
    assert "Version: 4.36.0" in plugin
    assert "site-intelligence-v4.36.0" in plugin
