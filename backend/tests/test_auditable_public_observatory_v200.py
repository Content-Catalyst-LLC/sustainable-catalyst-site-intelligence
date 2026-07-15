from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auditable_public_observatory import (
    AUDIT_ARTIFACTS,
    AUDIT_PACKET_SCHEMA,
    AUDIT_RECORD_SCHEMA,
    OBSERVATORY_SCHEMA,
    PUBLIC_WORKSPACES,
    ObservatoryError,
    audit_catalog,
    audit_packet,
    audit_packet_markdown,
    audit_record,
    canonical_json,
    integrity_digest,
    lineage_graph,
    observatory_diagnostics,
    observatory_profile,
    release_ledger,
    verification_contract,
    verify_payload,
)
from app.main import app
from app.saved_views import ALLOWED_VIEWS
from app.source_methodology_studio import METHODOLOGY_RECORDS, SOURCE_RECORDS

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_observatory_profile_is_version_aligned_and_public():
    payload = observatory_profile()
    assert payload["ok"] is True
    assert payload["schema"] == OBSERVATORY_SCHEMA
    assert payload["application_version"] == "2.5.0"
    assert payload["api_schema_version"] == "2.0"
    assert payload["release_status"] == "auditable-public-observatory"
    assert "integrity" in payload["positioning"].lower()


def test_observatory_registers_ten_public_workspaces():
    payload = observatory_profile()
    assert len(payload["workspaces"]) == 14
    assert payload["counts"]["workspaces"] == 14
    assert payload["workspaces"][0]["id"] == "observatory"
    assert {item["id"] for item in payload["workspaces"]} == {item["id"] for item in PUBLIC_WORKSPACES}


def test_audit_artifacts_cross_reference_registered_sources_and_methods():
    source_ids = {item["id"] for item in SOURCE_RECORDS}
    method_ids = {item["id"] for item in METHODOLOGY_RECORDS}
    assert len(AUDIT_ARTIFACTS) >= 10
    assert len({item["id"] for item in AUDIT_ARTIFACTS}) == len(AUDIT_ARTIFACTS)
    for artifact in AUDIT_ARTIFACTS:
        assert set(artifact.get("source_ids", [])).issubset(source_ids)
        assert set(artifact.get("methodology_ids", [])).issubset(method_ids)
        assert artifact["route"].startswith("/app/?view=")


def test_audit_record_digest_is_stable_and_scoped_to_core_fields():
    first = audit_record("country-intelligence")
    second = audit_record("country-intelligence")
    assert first["schema"] == AUDIT_RECORD_SCHEMA
    assert first["integrity"]["digest"] == second["integrity"]["digest"]
    core = {key: value for key, value in first.items() if key not in {"generated_at", "integrity"}}
    assert first["integrity"]["digest"] == integrity_digest(core)
    assert len(first["integrity"]["digest"]) == 64


def test_unknown_audit_record_is_rejected():
    with pytest.raises(ObservatoryError):
        audit_record("not-a-public-artifact")


def test_audit_catalog_contains_complete_records():
    payload = audit_catalog()
    assert payload["record_count"] == len(AUDIT_ARTIFACTS)
    assert len(payload["records"]) == payload["record_count"]
    assert all(record["application_version"] == "2.5.0" for record in payload["records"])
    assert all(record["integrity"]["algorithm"] == "sha256" for record in payload["records"])


def test_lineage_graph_links_sources_methods_artifacts_and_workspaces():
    payload = lineage_graph()
    node_types = {node["type"] for node in payload["nodes"]}
    relations = {edge["relation"] for edge in payload["edges"]}
    assert node_types == {"source", "methodology", "workspace", "audit-artifact"}
    assert {"supports", "governs", "documents"}.issubset(relations)
    assert len(payload["edges"]) > len(AUDIT_ARTIFACTS)
    core = {key: value for key, value in payload.items() if key not in {"ok", "generated_at", "integrity"}}
    assert payload["integrity"]["digest"] == integrity_digest(core)


def test_verification_contract_is_non_persistent_and_bounded():
    payload = verification_contract()
    assert payload["algorithm"] == "sha256"
    assert payload["persistence"] is False
    assert payload["sensitive_fields_rejected"] is True
    assert payload["maximum_payload_bytes"] == 262144
    assert "factual correctness" in payload["meaning"]["not_proven"]


def test_verify_payload_matches_expected_digest_without_persistence():
    data = {"schema": "example/1.0", "country": "KEN", "values": [0, None, 12.5]}
    expected = hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()
    payload = verify_payload(data, expected.upper())
    assert payload["digest"] == expected
    assert payload["expected_digest"] == expected
    assert payload["matched"] is True
    assert payload["persisted"] is False


def test_verify_payload_rejects_sensitive_fields_and_invalid_digest():
    with pytest.raises(ObservatoryError, match="sensitive"):
        verify_payload({"api_key": "not-accepted"})
    with pytest.raises(ObservatoryError, match="64-character"):
        verify_payload({"ok": True}, "abc")


def test_verify_payload_rejects_oversized_canonical_payload():
    with pytest.raises(ObservatoryError, match="exceeds"):
        verify_payload({"body": "x" * 262200})


def test_release_ledger_reaches_the_major_observatory_release():
    payload = release_ledger()
    assert payload["entries"][-1]["version"] == "2.5.0"
    assert payload["entries"][-1]["title"] == "Humanitarian, Conflict, and Displacement Observatory"
    assert len(payload["integrity"]["digest"]) == 64


def test_audit_packet_and_markdown_are_download_ready():
    payload = audit_packet()
    markdown = audit_packet_markdown()
    assert payload["schema"] == AUDIT_PACKET_SCHEMA
    assert payload["application_version"] == "2.5.0"
    assert len(payload["records"]) == len(AUDIT_ARTIFACTS)
    assert markdown.startswith("# Sustainable Catalyst Site Intelligence")
    assert "**Release:** v2.5.0 — Humanitarian, Conflict, and Displacement Observatory" in markdown
    assert "## Verification boundary" in markdown


def test_public_observatory_get_endpoints():
    paths = [
        "/public/observatory",
        "/public/observatory/catalog",
        "/public/observatory/audit/country-intelligence",
        "/public/observatory/lineage",
        "/public/observatory/verification",
        "/public/observatory/release-ledger",
        "/public/observatory/diagnostics",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.json()["application_version"] == "2.5.0", path
    assert client.get("/public/observatory/audit/unknown").status_code == 404


def test_public_observatory_verify_endpoint_is_structural_only():
    payload = {"schema": "example/1.0", "value": 0}
    digest = integrity_digest(payload)
    response = client.post("/public/observatory/verify", json={"payload": payload, "expected_digest": digest})
    assert response.status_code == 200
    assert response.json()["matched"] is True
    assert response.json()["persisted"] is False
    assert client.post("/public/observatory/verify", json={"expected_digest": digest}).status_code == 422
    assert client.post("/public/observatory/verify", json={"payload": {"secret": "x"}}).status_code == 422


def test_public_observatory_export_supports_json_and_markdown():
    json_response = client.get("/public/observatory/export?format=json")
    markdown_response = client.get("/public/observatory/export?format=markdown")
    invalid_response = client.get("/public/observatory/export?format=pdf")
    assert json_response.status_code == 200
    assert json_response.json()["schema"] == AUDIT_PACKET_SCHEMA
    assert markdown_response.status_code == 200
    assert markdown_response.headers["content-type"].startswith("text/markdown")
    assert "site-intelligence-audit-packet.md" in markdown_response.headers["content-disposition"]
    assert invalid_response.status_code == 422


def test_saved_view_contract_includes_observatory_route():
    assert "observatory" in ALLOWED_VIEWS
    assert ALLOWED_VIEWS["observatory"]["state_keys"] == []
    response = client.post(
        "/public/saved-views/validate",
        json={
            "schema": "sc-saved-view/1.0",
            "application_version": "2.5.0",
            "id": "sv-observatory",
            "name": "Audit workspace",
            "view": "observatory",
            "state": {},
            "created_at": "2026-07-11T00:00:00Z",
            "updated_at": "2026-07-11T00:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_frontend_registers_observatory_navigation_workspace_and_loader():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/app.css").read_text(encoding="utf-8")
    assert 'data-route="observatory"' in html
    assert 'id="auditablePublicObservatory"' in html
    assert "Every public output should be traceable" in html
    assert 'const APP_VERSION="2.5.0"' in js
    assert "function openAuditablePublicObservatory" in js
    assert 'route==="observatory"' in js
    assert 'apiWithRetry("/public/observatory/catalog"' in js
    assert "auditable-observatory" in css
    assert "observatory-audit-grid" in css


def test_wordpress_observatory_shortcode_and_modern_legacy_aliases():
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert "Version: 2.5.0" in php
    assert "const VERSION = '2.5.0';" in php
    assert "add_shortcode('sc_auditable_public_observatory'" in php
    assert "public function auditable_public_observatory_shortcode" in php
    assert "/app/?view=observatory" in php
    assert "LEGACY_SHORTCODE_REMOVAL_TARGET = 'fulfilled-in-2.0.0'" in php
    assert "LEGACY_SHORTCODE_COMPATIBILITY = 'modern-workspace-aliases'" in php
    assert "Sustainable Catalyst Global Country Intelligence" in php
    assert "Sustainable Catalyst Comparative Intelligence" in php
    assert "Sustainable Catalyst Earth Observation Studio" in php


def test_observatory_diagnostics_and_release_files_are_complete():
    diagnostics = observatory_diagnostics()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V200.json").read_text(encoding="utf-8"))
    assert diagnostics["ok"] is True
    assert all(diagnostics["checks"].values())
    assert diagnostics["secrets_exposed"] is False
    assert "**Current release:** v2.5.0" in readme
    assert "## 2.0.0 — Auditable Public Observatory" in changelog
    assert manifest["release"] == "2.0.0"
    assert manifest["schema"] == OBSERVATORY_SCHEMA
    assert (ROOT / "docs/AUDITABLE_PUBLIC_OBSERVATORY_V200.md").exists()
