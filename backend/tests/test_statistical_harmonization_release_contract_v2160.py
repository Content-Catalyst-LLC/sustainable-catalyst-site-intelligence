import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v2160_policy_and_registries_prohibit_hidden_harmonization():
    policy = json.loads((ROOT / "backend/data/statistical_harmonization_policy_v2160.json").read_text())
    units = json.loads((ROOT / "backend/data/unit_registry_v2160.json").read_text())
    geography = json.loads((ROOT / "backend/data/geography_compatibility_registry_v2160.json").read_text())
    assert policy["silent_normalization"] is False
    assert policy["silent_imputation"] is False
    assert policy["automatic_rankings"] is False
    assert len(units["units"]) >= 10 and len(units["currencies"]) >= 5
    assert any(item["status"] == "not-directly-comparable" for item in geography["compatibility_rules"])


def test_v2160_public_app_wordpress_and_backend_publish_harmonization_surfaces():
    main = (ROOT / "backend/app/main.py").read_text()
    index = (ROOT / "backend/public_app/index.html").read_text()
    app = (ROOT / "backend/public_app/assets/app.js").read_text()
    worker = (ROOT / "backend/public_app/service-worker.js").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    for marker in ["/public/harmonization", "/admin/harmonization/control-center", "/admin/harmonization/transform", "/admin/harmonization/workbench-handoff"]:
        assert marker in main
    assert 'data-route="harmonization"' in index and 'id="harmonizationStudio"' in index
    assert "SCHarmonizationV2160" in app
    assert "/app/assets/harmonization-v2160.js" in worker
    assert "Version: 2.24.0" in plugin
    assert "sc_public_comparable_series" in plugin
    assert "sc_statistical_harmonization_control_center" in plugin


def test_v2160_runtime_state_is_excluded_and_release_manifest_is_governed():
    assert not (ROOT / "backend/data/statistical_harmonization_v2160").exists()
    gitignore = (ROOT / ".gitignore").read_text()
    manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2160.json").read_text())
    assert "backend/data/statistical_harmonization_v2160/" in gitignore
    assert manifest["silent_normalization"] is False
    assert manifest["implicit_exchange_rates"] is False
    assert manifest["automatic_rankings"] is False
    assert "/public/harmonization/compare" in manifest["public_endpoints"]
