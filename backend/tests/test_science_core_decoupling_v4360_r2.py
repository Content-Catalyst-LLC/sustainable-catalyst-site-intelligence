from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import scientific_earth_systems_observatory as science
from app.main import app

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def unconfigured_settings():
    return SimpleNamespace(
        platform_core_enabled=False,
        platform_core_url="",
        platform_core_public_api_key="",
        scientific_earth_systems_enabled=True,
        scientific_earth_systems_timeout_seconds=9,
        scientific_earth_systems_cache_ttl_seconds=120,
    )


def test_local_science_discovery_remains_available_without_platform_core():
    payload = science.build_science_discovery(unconfigured_settings())
    assert payload["ok"] is True
    assert payload["version"] == "4.36.0"
    assert payload["release_lineage"] == "v4.36.0-r3"
    assert payload["contract"] == "science-core-decoupled-ocean-space-discovery"
    assert payload["local_discovery_available"] is True
    assert payload["core_records_optional"] is True
    assert payload["core_records_configured"] is False
    assert payload["local_workspace_count"] == 8
    assert [row["id"] for row in payload["domains"]] == ["earth", "ocean", "space"]
    assert {row["domain"] for row in payload["workspaces"]} == {"earth", "ocean", "space"}
    assert all(row["core_required"] is False for row in payload["workspaces"])
    assert any(row["id"] == "ocean-intelligence" for row in payload["workspaces"])
    assert {row["id"] for row in payload["workspaces"] if row["domain"] == "space"} >= {
        "orbital-earth", "lunar-planetary", "astronomy", "solar-system", "exoplanets", "seti"
    }


def test_public_science_discovery_route_is_network_free_and_public():
    response = CLIENT.get("/public/scientific-earth-systems/discovery")
    assert response.status_code == 200
    payload = response.json()
    assert payload["local_discovery_available"] is True
    assert payload["local_workspace_count"] == 8


def test_science_interface_contains_always_populated_domain_selector_and_optional_core_boundary():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    assert 'id="scienceWorkspaceSelect"' in html
    assert '<option value="earth">Earth</option>' in html
    assert '<option value="ocean">Ocean</option>' in html
    assert '<option value="space">Space</option>' in html
    assert 'id="scienceWorkspaceCards"' in html
    assert 'id="scienceCoreRecordNotice"' in html
    assert "Platform Core adds optional scientific-record" in html
    assert "it no longer gates access to Ocean or Space" in html


def test_science_browser_controller_launches_local_ocean_and_space_workspaces_without_core_records():
    js = (ROOT / "backend/public_app/assets/science-v240.js").read_text(encoding="utf-8")
    assert 'api("/public/scientific-earth-systems/discovery")' in js
    assert 'window.SCSIOceanObservationV4360?.open?.()' in js
    assert 'window.SCSIOrbitalEarthV4100?.enter?.()' in js
    assert 'window.SCSIPlanetaryV4200?.enter?.()' in js
    assert 'window.SCSIAstronomicalV4300?.enter?.()' in js
    assert 'window.SCSISolarSystemV4400?.enter?.()' in js
    assert 'qs("#astroExoplanets")?.click()' in js
    assert 'qs("#astroSeti")?.click()' in js
    assert 'coreControls(false)' in js
    assert "Earth, Ocean, and Space remain available" in js


def test_science_assets_are_mirrored_to_wordpress_plugin():
    for name in ("science-v240.js", "science-v240.css"):
        backend = ROOT / "backend/public_app/assets" / name
        wordpress = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets" / name
        assert backend.read_bytes() == wordpress.read_bytes()
