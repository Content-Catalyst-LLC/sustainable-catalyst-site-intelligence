#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.19.0"', 'RELEASE_NAME = "Cross-Domain Knowledge Graph and Relationship Explorer"'],
    "backend/app/config.py": ["knowledge_graph_enabled", "knowledge_graph_entities_path", "knowledge_graph_relationships_path", "knowledge_graph_aliases_path"],
    "backend/app/knowledge_graph_v2190.py": ['RELEASE_VERSION = "2.19.0"', 'SCHEMA_VERSION = "sc-site-intelligence-knowledge-graph/1.0"', "def register_entity(", "def register_relationship(", "def preview_reconciliation(", "def traverse(", "def shortest_path(", "def diagnostics(", "def export_subgraph(", "def platform_core_handoff("],
    "backend/app/main.py": ['"/public/knowledge-graph"', '"/public/knowledge-graph/entities"', '"/public/knowledge-graph/traverse"', '"/public/knowledge-graph/path"', '"/admin/knowledge-graph/control-center"', '"/admin/knowledge-graph/platform-core-handoff"'],
    "backend/data/knowledge_graph_policy_v2190.json": ['"version": "2.19.0"', "No causation inferred", "No automatic entity merging", "No individual tracking"],
    "backend/data/knowledge_graph_relationship_registry_v2190.json": ['"version": "2.19.0"', '"entity_types"', '"relationship_types"', '"supports"', '"conflicts_with"'],
    "backend/public_app/index.html": ['data-route="graph"', 'id="knowledgeGraphExplorer"', '/app/assets/graph-v2190.js?v=2.19.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.19.0"', 'graph:[', 'window.SCKnowledgeGraphV2190'],
    "backend/public_app/assets/graph-v2190.js": ['const VERSION="2.19.0"', 'window.SCKnowledgeGraphV2190', '/public/knowledge-graph', '/public/knowledge-graph/entities'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.19.0"', '"/app/assets/graph-v2190.css"', '"/app/assets/graph-v2190.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.19.0', 'sc_public_relationship_explorer', 'sc_knowledge_graph_control_center', 'public-relationship-explorer'],
    "scripts/knowledge_graph_v2190.py": ["summary", "methodology", "diagnostics", "export", "handoff"],
    "docs/V2190_CROSS_DOMAIN_KNOWLEDGE_GRAPH_RELATIONSHIP_EXPLORER.md": ["typed graph entities", "never merges entities automatically", "Graph proximity"],
    "docs/RELEASE_MANIFEST_V2190.json": ['"release": "2.19.0"', '"automatic_causation": false', '"automatic_entity_merge": false', '"individual_tracking": false'],
    "README.md": ["Current release:** v2.19.0 — Cross-Domain Knowledge Graph and Relationship Explorer", "/app/?view=graph"],
    "CHANGELOG.md": ["## 2.19.0 — Cross-Domain Knowledge Graph and Relationship Explorer"],
}
for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")

manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2190.json").read_text(encoding="utf-8"))
for key in [
    "automatic_causation",
    "automatic_entity_merge",
    "individual_tracking",
    "social_scoring",
    "military_targeting",
    "automatic_consequential_decision",
    "platform_core_write_performed",
]:
    if manifest.get(key) is not False:
        raise SystemExit(f"Knowledge-graph governance boundary must remain false: {key}")
for key in ["human_review_required", "relationship_evidence_required", "public_relationship_approval_required"]:
    if manifest.get(key) is not True:
        raise SystemExit(f"Knowledge-graph governance requirement must remain enabled: {key}")

runtime_paths = [
    ROOT / "backend/data/knowledge_graph_v2190",
    ROOT / "backend/data/evidence_synthesis_v2180",
    ROOT / "backend/data/model_governance_v2170",
    ROOT / "backend/data/statistical_harmonization_v2160",
    ROOT / "backend/data/spatial_evidence_v2150",
    ROOT / "backend/data/historical_archive_v2140",
]
for runtime in runtime_paths:
    if runtime.exists():
        raise SystemExit(f"Writable runtime state must not be packaged: {runtime.relative_to(ROOT)}")

for relative in [
    "backend/data/connector_operations_state_v2130.json",
    "backend/data/connector_operations_history_v2130.jsonl",
    "backend/data/connector_operations_quarantine_v2130.jsonl",
    "backend/data/country_last_known_good.json",
    "backend/data/platform_core_queue.jsonl",
]:
    if (ROOT / relative).exists():
        raise SystemExit(f"Writable runtime file must not be packaged: {relative}")

for path in ROOT.rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
        raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")
    if path.is_file() and path.suffix in {".pyc", ".pyo"}:
        raise SystemExit(f"Generated Python file must not be packaged: {path.relative_to(ROOT)}")

print("Site Intelligence v2.19.0 release contract passed.")
