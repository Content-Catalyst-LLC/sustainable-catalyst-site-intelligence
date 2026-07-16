#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHECKS={
"backend/app/version.py":['APP_VERSION = "2.20.0"','RELEASE_NAME = "Intelligence Publishing and Story Map Studio"'],
"backend/app/config.py":["intelligence_publishing_enabled","intelligence_publishing_projects_path","intelligence_publishing_versions_path"],
"backend/app/intelligence_publishing_v2200.py":['RELEASE_VERSION = "2.20.0"','SCHEMA_VERSION = "sc-site-intelligence-publication-studio/1.0"',"def create_project(","def add_block(","def decide_review(","def publish_project(","def story_map(","def export_publication(","def wordpress_handoff("],
"backend/app/main.py":['"/public/intelligence-publishing"','"/public/intelligence-publications"','"/admin/intelligence-publishing/control-center"','"/admin/intelligence-publishing/projects/{project_id}/publish"'],
"backend/data/intelligence_publishing_policy_v2200.json":['"version": "2.20.0"',"human editorial approval","does not establish causation","read-only"],
"backend/public_app/index.html":['data-route="publishing"','id="intelligencePublishingStudio"','/app/assets/publishing-v2200.js?v=2.20.0'],
"backend/public_app/assets/app.js":['const APP_VERSION="2.20.0"','publishing:[','window.SCIntelligencePublishingV2200'],
"backend/public_app/assets/publishing-v2200.js":['const VERSION="2.20.0"','window.SCIntelligencePublishingV2200','/public/intelligence-publications'],
"backend/public_app/service-worker.js":['const RELEASE="2.20.0"','"/app/assets/publishing-v2200.css"','"/app/assets/publishing-v2200.js"'],
"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":['Version: 2.20.0','sc_public_intelligence_publications','sc_intelligence_publishing_control_center','sc_intelligence_publication'],
"scripts/intelligence_publishing_v2200.py":["summary","methodology","diagnostics","story-map","handoff"],
"docs/V2200_INTELLIGENCE_PUBLISHING_STORY_MAP_STUDIO.md":["human editorial decision","do not establish causation","read-only WordPress handoff"],
"docs/RELEASE_MANIFEST_V2200.json":['"release": "2.20.0"','"automatic_publication": false','"fabricated_sources": false','"wordpress_write_performed": false'],
"README.md":["Current release:** v2.20.0 — Intelligence Publishing and Story Map Studio","/app/?view=publishing"],
"CHANGELOG.md":["## 2.20.0 — Intelligence Publishing and Story Map Studio"],
}
for rel,markers in CHECKS.items():
    path=ROOT/rel
    if not path.exists(): raise SystemExit(f"Missing release file: {rel}")
    text=path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text: raise SystemExit(f"Missing release marker {marker!r} in {rel}")
manifest=json.loads((ROOT/'docs/RELEASE_MANIFEST_V2200.json').read_text())
for key in ["automatic_publication","fabricated_sources","automatic_causal_inference","hidden_conflict_suppression","wordpress_write_performed","pdf_binary_generated"]:
    if manifest.get(key) is not False: raise SystemExit(f"Publishing governance boundary must remain false: {key}")
for key in ["human_editorial_approval_required","explicit_publish_confirmation_required","immutable_publication_versions","source_and_evidence_references_preserved"]:
    if manifest.get(key) is not True: raise SystemExit(f"Publishing governance requirement must remain enabled: {key}")
runtime=[ROOT/'backend/data/intelligence_publishing_v2200',ROOT/'backend/data/knowledge_graph_v2190',ROOT/'backend/data/evidence_synthesis_v2180',ROOT/'backend/data/model_governance_v2170',ROOT/'backend/data/statistical_harmonization_v2160',ROOT/'backend/data/spatial_evidence_v2150',ROOT/'backend/data/historical_archive_v2140']
for path in runtime:
    if path.exists(): raise SystemExit(f"Writable runtime state must not be packaged: {path.relative_to(ROOT)}")
for rel in ["backend/data/connector_operations_state_v2130.json","backend/data/connector_operations_history_v2130.jsonl","backend/data/connector_operations_quarantine_v2130.jsonl","backend/data/country_last_known_good.json","backend/data/platform_core_queue.jsonl"]:
    if (ROOT/rel).exists(): raise SystemExit(f"Writable runtime file must not be packaged: {rel}")
for path in ROOT.rglob('*'):
    if '.git' in path.parts: continue
    if path.is_dir() and path.name in {'__pycache__','.pytest_cache'}: raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")
    if path.is_file() and path.suffix in {'.pyc','.pyo'}: raise SystemExit(f"Generated Python file must not be packaged: {path.relative_to(ROOT)}")
print("Site Intelligence v2.20.0 release contract passed.")
