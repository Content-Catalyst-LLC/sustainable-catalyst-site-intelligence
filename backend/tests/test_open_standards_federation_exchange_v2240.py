from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.federation_exchange_v2240 import InstitutionalDataExchange, FEDERATION_SCHEMA
from app.main import app


def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "federation"
    base = Path(__file__).resolve().parents[1] / "data"
    return Settings(
        federation_institutions_path=str(root / "institutions.jsonl"),
        federation_records_path=str(root / "records.jsonl"),
        federation_manifests_path=str(root / "manifests.jsonl"),
        federation_imports_path=str(root / "imports.jsonl"),
        federation_trust_path=str(root / "trust.jsonl"),
        federation_policy_path=str(base / "federation_policy_v2240.json"),
        federation_context_path=str(base / "federation_context_v2240.json"),
        federation_signing_key="test-secret",
        federation_signing_key_id="test-key",
    )


def seed(center: InstitutionalDataExchange):
    institution = center.register_institution({
        "institution_id": "sustainable-catalyst",
        "name": "Sustainable Catalyst",
        "homepage": "https://sustainablecatalyst.com",
        "catalog_url": "https://example.test/public/institutional-data-exchange/catalog",
        "visibility": "public",
    })
    record = center.register_record({
        "institution_id": institution["institution_id"],
        "record_id": "dataset:climate:1",
        "record_type": "dataset",
        "title": "Climate Evidence Dataset",
        "description": "A source-aware test dataset.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "hosting_mode": "hosted",
        "visibility": "public",
        "provenance": {"source_ids": ["source:1"]},
        "distributions": [{"title": "JSON", "access_url": "https://example.test/data.json", "media_type": "application/json"}],
    })
    return institution, record


def test_register_institution_and_catalog_record(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, record = seed(center)
    assert institution["visibility"] == "public"
    assert record["record_type"] == "dataset"
    assert record["hosting_mode"] == "hosted"
    assert len(record["sha256"]) == 64


def test_record_requires_registered_institution_and_explicit_mode(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    with pytest.raises(ValueError, match="not registered"):
        center.register_record({"institution_id": "missing", "title": "No owner"})
    center.register_institution({"institution_id": "one", "name": "One"})
    with pytest.raises(ValueError, match="hosting_mode"):
        center.register_record({"institution_id": "one", "title": "Bad", "hosting_mode": "copied"})


def test_signed_manifest_and_signature_verification(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    center.set_trust_policy(institution["institution_id"], {
        "trust_state": "trusted", "require_signature": True,
        "expected_key_id": "test-key", "allowed_record_types": ["dataset"],
        "allowed_hosting_modes": ["hosted", "mirrored", "referenced"],
    })
    manifest = center.build_manifest(institution["institution_id"], {"sign": True, "public_only": True})
    result = center.validate_manifest(manifest, key="test-secret")
    assert manifest["schema"] == FEDERATION_SCHEMA
    assert result["valid"] is True
    assert result["signature_valid"] is True
    assert result["identity_verified"] is False


def test_tampered_manifest_fails_signature(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    center.set_trust_policy(institution["institution_id"], {"trust_state": "trusted", "expected_key_id": "test-key"})
    manifest = center.build_manifest(institution["institution_id"], {"sign": True})
    manifest["catalog"][0]["title"] = "Tampered"
    result = center.validate_manifest(manifest, key="test-secret")
    assert result["valid"] is False
    assert "signature verification failed" in result["errors"]


def test_blocked_trust_policy_quarantines_import(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    center.set_trust_policy(institution["institution_id"], {"trust_state": "blocked", "require_signature": False})
    manifest = center.build_manifest(institution["institution_id"], {})
    preview = center.import_preview(manifest)
    assert preview["validation"]["valid"] is False
    with pytest.raises(ValueError, match="confirm=true"):
        center.accept_import(manifest, {})
    receipt = center.accept_import(manifest, {"confirm": True})
    assert receipt["status"] == "quarantined"
    assert receipt["records_materialized"] is False


def test_import_preview_never_fetches_or_imports_automatically(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    center.set_trust_policy(institution["institution_id"], {"trust_state": "trusted", "require_signature": False})
    manifest = center.build_manifest(institution["institution_id"], {})
    preview = center.import_preview(manifest)
    assert preview["automatic_import"] is False
    assert preview["remote_fetch_performed"] is False
    assert preview["requires_confirm"] is True


def test_manifest_publication_requires_human_confirmation(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    manifest = center.build_manifest(institution["institution_id"], {"sign": True, "public_only": True})
    with pytest.raises(ValueError, match="confirm=true"):
        center.publish_manifest(manifest["manifest_id"], {})
    published = center.publish_manifest(manifest["manifest_id"], {"confirm": True, "published_by": "reviewer"})
    assert published["status"] == "published" and published["visibility"] == "public"
    assert center.public_summary()["summary"]["manifest_count"] == 1


def test_dcat_geojson_and_csv_exports(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    seed(center)
    dcat = json.loads(center.export_catalog("jsonld"))
    assert dcat["record_count"] == 1 and dcat["dataset"][0]["license"]
    geojson = json.loads(center.export_catalog("geojson"))
    assert geojson["type"] == "FeatureCollection"
    csv_body = center.export_catalog("csv").decode()
    assert "record_id,record_type" in csv_body and "dataset:climate:1" in csv_body


def test_public_boundary_excludes_trust_imports_and_private_records(tmp_path):
    center = InstitutionalDataExchange(settings(tmp_path))
    institution, _ = seed(center)
    center.register_record({"institution_id": institution["institution_id"], "title": "Private", "visibility": "private", "hosting_mode": "referenced"})
    center.set_trust_policy(institution["institution_id"], {"trust_state": "trusted", "require_signature": False})
    public = center.public_summary()
    assert public["summary"]["record_count"] == 1
    assert "trust_policies" not in public and "imports" not in public
    assert public["governance"]["automatic_import"] is False
    assert public["governance"]["identity_verified_by_signature"] is False


def test_public_and_admin_api_contracts(tmp_path):
    current = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: current
    try:
        client = TestClient(app)
        created = client.post("/admin/institutional-data-exchange/institutions", json={"institution_id": "open-lab", "name": "Open Lab", "visibility": "public"})
        assert created.status_code == 200
        record = client.post("/admin/institutional-data-exchange/records", json={"institution_id": "open-lab", "record_id": "publication:1", "record_type": "publication", "title": "Open Brief", "license": "CC BY 4.0", "hosting_mode": "referenced", "visibility": "public"})
        assert record.status_code == 200
        public = client.get("/public/institutional-data-exchange")
        assert public.status_code == 200 and public.json()["version"] == "3.6.1"
        catalog = client.get("/public/institutional-data-exchange/catalog?format=jsonld")
        assert catalog.status_code == 200 and catalog.headers["content-type"].startswith("application/ld+json")
        control = client.get("/admin/institutional-data-exchange/control-center")
        assert control.status_code == 200 and control.json()["schema"].startswith("sc-site-intelligence-federation")
    finally:
        app.dependency_overrides.clear()
