from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.country_evidence_presentation_v43525 import build_country_presentation, present_indicator, readiness
from app.main import app
from app.release_health_v43525 import deployment_verification

ROOT = Path(__file__).resolve().parents[2]


def test_world_bank_structural_electricity_is_not_presented_as_current_supply():
    row = present_indicator({
        "id": "EG.ELC.ACCS.ZS",
        "canonical_observation": {
            "presentation_label": "HARMONIZED BENCHMARK",
            "transport_state": "live",
            "source": {"source_id": "world_bank", "authority_class": "international-harmonized"},
            "semantics": {
                "concept_id": "electricity_structural_access",
                "current_condition_claim_allowed": False,
                "display_note": "Structural electricity access does not represent current electricity availability, outage status, hours of service, grid reliability, or generator dependence.",
            },
        },
    })
    assert row["role_label"] == "HARMONIZED BENCHMARK"
    assert row["scope_label"] == "STRUCTURAL ACCESS BASELINE"
    assert row["current_condition_claim_allowed"] is False
    assert row["condition_status"] == "not-established-by-this-indicator"
    assert "does not represent current electricity availability" in row["interpretation_note"]
    assert row["transport_state"] == "live"


def test_palestine_presentation_declares_authority_and_operational_boundary():
    payload = build_country_presentation({"code": "PSE", "name": "Palestine"}, [], missing_indicators=[])
    assert "PCBS is preferred" in payload["authority_summary"]
    assert "structural access percentage cannot establish present electricity" in payload["operational_boundary"]
    assert [row["id"] for row in payload["layers"]] == ["operational", "official", "international-benchmark", "reconciliation"]


def test_country_presentation_readiness_is_network_free_and_release_blocking():
    payload = readiness()
    assert payload["ok"] is True
    assert payload["network_calls_performed"] is False
    assert payload["upstream_health_release_blocking"] is False
    assert payload["checks"]["transport_live_does_not_upgrade_evidence"] is True
    assert payload["checks"]["automatic_blending_not_presented"] is True


def test_country_workspace_exposes_authoritative_evidence_hierarchy_and_conditions_boundary():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    css = (ROOT / "backend/public_app/assets/country-presentation-v43525.css").read_text(encoding="utf-8")
    assert "COUNTRY INTELLIGENCE BRIEF" in html
    assert 'id="countryEvidenceStatusTitle"' in html
    assert 'id="countryOperationalSummary"' in html
    assert "Operational evidence is separate from structural statistics" in html
    assert "OFFICIAL, PUBLISHED & COMPARATIVE INDICATORS" in html
    assert "renderCountryEvidenceHierarchy" in js
    assert "renderCountryIndicatorCard" in js
    assert "HARMONIZED BENCHMARK" in js
    assert "country-indicator-structural" in css
    assert "4.0 Direction" not in html


def test_reconciliation_ui_prefers_publisher_name_over_internal_source_id():
    js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    py = (ROOT / "backend/app/country_evidence_reconciliation_v43522.py").read_text(encoding="utf-8")
    assert 'row.selected_source_name||row.selected_source_id' in js
    assert '"selected_source_name"' in py


def test_deployment_verification_requires_country_evidence_presentation_plane():
    payload = deployment_verification(Settings(_env_file=None))
    assert payload["ok"] is True
    assert "/public/country-evidence-presentation/readiness" in payload["required_routes"]
    assert len(payload["required_routes"]) == 19
    assert payload["checks"]["country_evidence_presentation_ready"] is True
    assert payload["checks"]["structural_electricity_not_operational_truth"] is True
    assert payload["checks"]["harmonized_benchmark_role_explicit"] is True
    client = TestClient(app)
    response = client.get("/public/country-evidence-presentation/readiness")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_runtime_release_is_v43525_and_new_css_is_loaded():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-scsi-release="4.35.25"' in html
    assert 'country-presentation-v43525.css?v=4.35.25' in html
    assert 'const APP_VERSION="4.35.25"' in app_js
    assert "Version: 4.35.25" in plugin
