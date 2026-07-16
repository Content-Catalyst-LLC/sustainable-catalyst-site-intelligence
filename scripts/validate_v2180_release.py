#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.18.0"', 'RELEASE_NAME = "Evidence Synthesis, Claims, and Contradiction Review"'],
    "backend/app/config.py": ["evidence_synthesis_enabled", "evidence_synthesis_claims_path", "evidence_synthesis_syntheses_path", "evidence_synthesis_uncertainty_path"],
    "backend/app/evidence_synthesis_v2180.py": ['RELEASE_VERSION = "2.18.0"', 'SCHEMA_VERSION = "sc-site-intelligence-evidence-synthesis/1.0"', "def register_claim(", "def add_evidence(", "def review_claim(", "def contradiction_review(", "def synthesize(", "def export_packet(", "def handoff("],
    "backend/app/main.py": ['"/public/evidence-synthesis"', '"/public/claims"', '"/public/claims/{claim_id}/contradictions"', '"/admin/evidence-synthesis/control-center"', '"/admin/evidence-synthesis/handoff"'],
    "backend/data/evidence_synthesis_policy_v2180.json": ['"version": "2.18.0"', "No fabricated evidence", "No suppression of conflicting evidence", "No public synthesis without human review"],
    "backend/public_app/index.html": ['data-route="evidence"', 'id="evidenceSynthesisStudio"', '/app/assets/evidence-v2180.js?v=2.18.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.18.0"', 'evidence:[', 'window.SCEvidenceV2180'],
    "backend/public_app/assets/evidence-v2180.js": ['const VERSION="2.18.0"', 'window.SCEvidenceV2180', '/public/evidence-synthesis', '/public/claims'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.18.0"', '"/app/assets/evidence-v2180.css"', '"/app/assets/evidence-v2180.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.18.0', 'sc_public_evidence_synthesis', 'sc_evidence_synthesis_control_center', 'public-evidence-synthesis'],
    "scripts/evidence_synthesis_v2180.py": ["summary", "methodology", "diagnostics", "handoff"],
    "docs/V2180_EVIDENCE_SYNTHESIS_CLAIMS_CONTRADICTION_REVIEW.md": ["supporting, qualifying, conflicting, or contextual", "deterministic grounded template", "Knowledge Library or Research Librarian"],
    "docs/RELEASE_MANIFEST_V2180.json": ['"release": "2.18.0"', '"fabricated_evidence_allowed": false', '"hidden_contradictions_allowed": false', '"external_ai_default_enabled": false'],
    "README.md": ["Current release:** v2.18.0 — Evidence Synthesis, Claims, and Contradiction Review", "/app/?view=evidence"],
    "CHANGELOG.md": ["## 2.18.0 — Evidence Synthesis, Claims, and Contradiction Review"],
}
for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")
manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2180.json").read_text())
for key in ["fabricated_evidence_allowed", "hidden_contradictions_allowed", "automatic_causal_determination", "automatic_consequential_decision", "individual_targeting", "external_ai_default_enabled"]:
    if manifest.get(key) is not False:
        raise SystemExit(f"Evidence-synthesis governance boundary must remain false: {key}")
if not manifest.get("human_review_required") or not manifest.get("public_claim_approval_required") or not manifest.get("public_synthesis_approval_required"):
    raise SystemExit("Human review and public approval requirements must remain enabled.")
runtime = ROOT / "backend/data/evidence_synthesis_v2180"
if runtime.exists():
    raise SystemExit("Writable evidence-synthesis state must not be packaged.")
for path in ROOT.rglob("*"):
    if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
        raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")
print("Site Intelligence v2.18.0 release contract passed.")
