from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_markers():
    checks = {
        "backend/app/version.py": ["3.6.1", "Connected Public Intelligence and Evidence Platform"],
        "backend/app/federation_exchange_v2240.py": ["class InstitutionalDataExchange", "def build_manifest(", "def validate_manifest(", "def accept_import("],
        "backend/public_app/index.html": ["data-route=\"federation\"", "id=\"institutionalDataExchangeStudio\""],
        "backend/public_app/service-worker.js": ["/app/assets/federation-v2240.js", "/app/assets/federation-v2240.css"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.6.1", "sc_public_institutional_data_exchange", "sc_institutional_data_exchange_control_center"],
        "README.md": ["Current release:** v3.6.1 — Connected Public Intelligence and Evidence Platform"],
    }
    for rel, markers in checks.items():
        text = (ROOT / rel).read_text()
        for marker in markers:
            assert marker in text, f"{rel}: {marker}"


def test_governance_manifest_blocks_unsafe_federation_claims():
    data = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2240.json").read_text())
    assert data["record_types"] == 6 and data["hosting_modes"] == 3
    assert data["dcat_compatible_jsonld"] is True
    assert data["signed_manifests"] is True
    assert data["trust_policies"] is True
    assert data["automatic_remote_fetch"] is False
    assert data["automatic_import"] is False
    assert data["automatic_remote_write"] is False
    assert data["signature_proves_identity"] is False
    assert data["public_private_records_exposed"] is False
    assert data["individual_tracking"] is False


def test_public_app_loader_and_wordpress_proxy():
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text()
    federation_js = (ROOT / "backend/public_app/assets/federation-v2240.js").read_text()
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    wp_js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    assert "SCInstitutionalFederationV2240" in app_js and "SCInstitutionalFederationV2240" in federation_js
    assert "public-institutional-data-exchange" in php
    assert "institutional-data-exchange" in wp_js
