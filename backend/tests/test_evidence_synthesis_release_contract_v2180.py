from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_files_and_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.6.2"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/config.py": ["evidence_synthesis_enabled", "evidence_synthesis_claims_path", "evidence_synthesis_syntheses_path"],
        "backend/app/evidence_synthesis_v2180.py": ['RELEASE_VERSION = "3.6.2"', "def register_claim(", "def add_evidence(", "def contradiction_review(", "def synthesize("],
        "backend/app/main.py": ['"/public/evidence-synthesis"', '"/public/claims"', '"/admin/evidence-synthesis/control-center"', '"/admin/evidence-synthesis/handoff"'],
        "backend/data/evidence_synthesis_policy_v2180.json": ['"version": "3.6.2"', "No fabricated evidence", "No suppression of conflicting evidence"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, (relative, marker)


def test_writable_evidence_state_is_not_packaged():
    assert not (ROOT / "backend/data/evidence_synthesis_v2180").exists()


def test_public_app_wordpress_and_offline_contract():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    feature_js = (ROOT / "backend/public_app/assets/evidence-v2180.js").read_text(encoding="utf-8")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="evidence"' in html and 'id="evidenceSynthesisStudio"' in html
    assert 'window.SCEvidenceV2180' in app_js and '/public/evidence-synthesis' in feature_js
    assert 'evidence-v2180.js' in worker and 'evidence-v2180.css' in worker
    assert 'sc_public_evidence_synthesis' in php and 'sc_evidence_synthesis_control_center' in php


def test_release_docs_and_governance_manifest():
    import json
    manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2180.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "2.19.0"
    assert manifest["fabricated_evidence_allowed"] is False
    assert manifest["hidden_contradictions_allowed"] is False
    assert manifest["human_review_required"] is True
    assert (ROOT / "docs/V2180_EVIDENCE_SYNTHESIS_CLAIMS_CONTRADICTION_REVIEW.md").exists()
