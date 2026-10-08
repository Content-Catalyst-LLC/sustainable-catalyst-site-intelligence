from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.version import APP_VERSION, RELEASE_NAME
from app.production_truth_v3231 import public_production_truth
from app.route_registry_v4430 import capability_manifest

client = TestClient(app)
ROUTES = {
    "economics": ("#economicsStudio", "/public/economics-sustainability", "SCEconomicsV220"),
    "law": ("#lawStudio", "/public/international-law-observatory", "SCLawV230"),
    "science": ("#scienceStudio", "/public/scientific-earth-systems", "SCScienceV240"),
    "humanitarian": ("#humanitarianStudio", "/public/humanitarian-conflict-displacement", "SCHumanitarianV250"),
    "resources": ("#resourceStudio", "/public/trade-energy-resources", "SCResourcesV260"),
    "dossiers": ("#dossierStudio", "/public/intelligence-dossiers", "SCDossiersV270"),
}


def repo_root():
    return Path(__file__).resolve().parents[2]


def test_release_identity_and_route_inventory_unchanged():
    assert APP_VERSION == "4.55.3.2.2"
    assert RELEASE_NAME == "Browser API Transport & CORS Repair"
    m = capability_manifest(app.routes)
    assert m["registry_version"] == "2.6.2"
    assert m["route_count"] == 1518
    assert m["modularized_route_count"] == 209
    assert m["capability_count"] == 31
    assert m["unclassified_route_count"] == 0


def test_production_truth_uses_real_workspace_surfaces_and_endpoint_families():
    directory = public_production_truth()
    assert directory["version"] == "4.55.3.2.2"
    contracts = {row["route_id"]: row for row in directory["routes"]}
    for route, (selector, endpoint, controller) in ROUTES.items():
        row = contracts[route]
        assert selector in row["surface_selectors"]
        assert endpoint in row["endpoint_families"]
        assert row["controller"] == controller
        assert row["publicly_navigable"] is True


def test_stale_workspace_selectors_are_gone():
    text = (repo_root()/"backend/app/production_truth_v3231.py").read_text()
    for stale in ["#economicsWorkspace", "#lawWorkspace", "#scienceWorkspace", "#humanitarianWorkspace", "#resourcesWorkspace", "#dossiersWorkspace"]:
        assert stale not in text


def test_runtime_repair_asset_is_packaged_and_current():
    root = repo_root()
    runtime = (root/"backend/public_app/assets/workspace-runtime-repair-v4551.js").read_text()
    index = (root/"backend/public_app/index.html").read_text()
    assert 'const VERSION="4.55.1"' in runtime
    for route, (selector, _, controller) in ROUTES.items():
        assert route in runtime
        assert selector in runtime
        assert controller in runtime
    assert '/app/assets/workspace-runtime-repair-v4551.js?v=4.55.3.2.2' in index
    assert index.index('workspace-runtime-repair-v4551.js') < index.index('production-truth-v3231.js')


def test_production_truth_browser_contract_uses_active_release_not_4390():
    text = (repo_root()/"backend/public_app/assets/production-truth-v3231.js").read_text()
    assert 'APP_ROOT.dataset.scsiRelease||"4.55.3.2.2"' in text
    assert 'const VERSION="4.39.0"' not in text


def test_router_uses_shared_resilient_core_workspace_opener():
    text = (repo_root()/"backend/public_app/assets/app.js").read_text()
    assert 'async function openCoreWorkspace(route)' in text
    for route in ROUTES:
        assert f'openCoreWorkspace("{route}")' in text
    assert 'SCSIWorkspaceRuntimeRepairV4551' in text


def test_dossiers_resources_and_humanitarian_keep_shell_visible_on_optional_failures():
    root = repo_root()/"backend/public_app/assets"
    dossier = (root/"dossiers-v270.js").read_text()
    resources = (root/"resources-v260.js").read_text()
    humanitarian = (root/"humanitarian-v250.js").read_text()
    assert "Dossier facets unavailable; opening resilient shell" in dossier
    assert "panel.hidden=false" in dossier and "return true" in dossier
    assert "Resource country catalog unavailable; continuing" in resources
    assert "panel.hidden=false" in resources and "return true" in resources
    assert "s.hidden=false" in humanitarian and "return true" in humanitarian


def test_all_six_primary_backend_families_respond_without_404():
    probes = [
        "/public/intelligence-dossiers/facets",
        "/public/economics-sustainability",
        "/public/international-law-observatory",
        "/public/scientific-earth-systems/discovery",
        "/public/humanitarian-conflict-displacement/records?limit=1",
        "/public/trade-energy-resources/records?limit=1",
    ]
    for path in probes:
        response = client.get(path)
        assert response.status_code == 200, (path, response.text[:300])
        assert response.json().get("ok") is True


def test_wordpress_remains_thin_shell_and_version_aligned():
    php = (repo_root()/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "Version: 4.55.3.2.2" in php
    assert "const VERSION = '4.55.3.2.2';" in php
    assert "const RELEASE_ID = 'site-intelligence-v4.55.3.2.2';" in php
    assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in php
