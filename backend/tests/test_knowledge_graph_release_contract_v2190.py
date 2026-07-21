from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_files_and_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.7.2"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/config.py": ["knowledge_graph_enabled", "knowledge_graph_entities_path", "knowledge_graph_relationships_path", "knowledge_graph_aliases_path"],
        "backend/app/knowledge_graph_v2190.py": ['RELEASE_VERSION = "3.7.2"', "def register_entity(", "def register_relationship(", "def traverse(", "def shortest_path(", "def preview_reconciliation(", "def platform_core_handoff("],
        "backend/app/main.py": ['"/public/knowledge-graph"', '"/public/knowledge-graph/traverse"', '"/public/knowledge-graph/path"', '"/admin/knowledge-graph/control-center"', '"/admin/knowledge-graph/platform-core-handoff"'],
        "backend/data/knowledge_graph_policy_v2190.json": ['"version": "3.7.2"', "No causation inferred", "No automatic entity merging", "No individual tracking"],
        "backend/data/knowledge_graph_relationship_registry_v2190.json": ['"version": "3.7.2"', '"entity_types"', '"relationship_types"', '"supports"', '"conflicts_with"'],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, (relative, marker)


def test_writable_graph_state_is_not_packaged():
    assert not (ROOT / "backend/data/knowledge_graph_v2190").exists()


def test_public_app_wordpress_and_offline_contract():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    feature_js = (ROOT / "backend/public_app/assets/graph-v2190.js").read_text(encoding="utf-8")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="graph"' in html and 'id="knowledgeGraphExplorer"' in html
    assert 'window.SCKnowledgeGraphV2190' in app_js and '/public/knowledge-graph' in feature_js
    assert 'graph-v2190.js' in worker and 'graph-v2190.css' in worker
    assert 'sc_public_relationship_explorer' in php and 'sc_knowledge_graph_control_center' in php


def test_release_docs_and_governance_manifest():
    manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2190.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "2.19.0"
    assert manifest["automatic_causation"] is False
    assert manifest["automatic_entity_merge"] is False
    assert manifest["individual_tracking"] is False
    assert manifest["relationship_evidence_required"] is True
    assert (ROOT / "docs/V2190_CROSS_DOMAIN_KNOWLEDGE_GRAPH_RELATIONSHIP_EXPLORER.md").exists()
