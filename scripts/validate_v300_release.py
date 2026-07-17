from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    "backend/app/version.py": ['APP_VERSION = "3.0.0"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
    "backend/app/connected_public_intelligence_v300.py": ["class ConnectedPublicIntelligencePlatform", "def search(", "def context(", "def provenance(", "def lifecycle(", "def export("],
    "backend/app/main.py": ["/public/connected-intelligence", "/public/connected-intelligence/search", "/public/connected-intelligence/context/{record_id:path}", "/admin/connected-intelligence/control-center"],
    "backend/public_app/index.html": ['data-route="platform"', 'id="connectedPlatformStudio"', "platform-v300.js?v=3.0.0", "platform-v300.css?v=3.0.0"],
    "backend/public_app/service-worker.js": ['const RELEASE="3.0.0"', "platform-v300.js", "platform-v300.css"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.0.0", "sc_connected_public_intelligence", "sc_connected_intelligence_control_center"],
    "README.md": ["Current release:** v3.0.0 — Connected Public Intelligence and Evidence Platform"],
}
for relative, markers in checks.items():
    text = (ROOT / relative).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"{relative}: missing {marker}")
policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V300.json").read_text(encoding="utf-8"))
for key in ["unified_public_search", "shared_record_context", "digest_linked_provenance", "source_to_publication_lifecycle", "account_free_public_access", "private_records_excluded", "conflicting_evidence_preserved", "human_review_preserved"]:
    if policy.get(key) is not True:
        raise SystemExit(f"Release policy requires {key}=true")
for key in ["automatic_publication", "automatic_remote_delivery_claim", "causation_from_graph_structure", "hidden_ranking", "persistent_search_cluster_claim", "individual_tracking"]:
    if policy.get(key) is not False:
        raise SystemExit(f"Release policy requires {key}=false")
for path in [
    ROOT / "backend/data/production_governance_v2250",
    ROOT / "backend/data/federation_exchange_v2240",
    ROOT / "backend/data/cross_platform_workflows_v2230",
    ROOT / "backend/data/institutional_workspaces_v2220",
    ROOT / "backend/data/scheduled_monitoring_v2210",
    ROOT / "backend/data/intelligence_publishing_v2200",
    ROOT / "backend/data/knowledge_graph_v2190",
    ROOT / "backend/data/evidence_synthesis_v2180",
    ROOT / "backend/data/model_governance_v2170",
    ROOT / "backend/data/statistical_harmonization_v2160",
    ROOT / "backend/data/spatial_evidence_v2150",
    ROOT / "backend/data/historical_archive_v2140",
]:
    if path.exists():
        raise SystemExit(f"Writable runtime state is present: {path.relative_to(ROOT)}")
print("Site Intelligence v3.0.0 release contract passed.")
