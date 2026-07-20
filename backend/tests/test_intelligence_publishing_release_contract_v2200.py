from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_files_and_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.1.3"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/config.py": ["intelligence_publishing_enabled", "intelligence_publishing_projects_path", "intelligence_publishing_versions_path"],
        "backend/app/intelligence_publishing_v2200.py": ['RELEASE_VERSION = "3.1.3"', "def create_project(", "def add_block(", "def decide_review(", "def publish_project(", "def story_map(", "def export_publication(", "def wordpress_handoff("],
        "backend/app/main.py": ['"/public/intelligence-publishing"', '"/public/intelligence-publications"', '"/admin/intelligence-publishing/control-center"', '"/admin/intelligence-publishing/projects/{project_id}/publish"'],
        "backend/data/intelligence_publishing_policy_v2200.json": ['"version": "3.1.3"', "human editorial approval", "does not establish causation", "read-only"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, (relative, marker)


def test_writable_publishing_state_is_not_packaged():
    assert not (ROOT / "backend/data/intelligence_publishing_v2200").exists()


def test_public_app_wordpress_and_offline_contract():
    html = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
    feature_js = (ROOT / "backend/public_app/assets/publishing-v2200.js").read_text(encoding="utf-8")
    worker = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
    php = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    assert 'data-route="publishing"' in html and 'id="intelligencePublishingStudio"' in html
    assert 'window.SCIntelligencePublishingV2200' in app_js and '/public/intelligence-publications' in feature_js
    assert 'publishing-v2200.js' in worker and 'publishing-v2200.css' in worker
    assert 'sc_public_intelligence_publications' in php and 'sc_intelligence_publishing_control_center' in php


def test_release_docs_and_governance_manifest():
    manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2200.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "2.20.0"
    assert manifest["automatic_publication"] is False
    assert manifest["human_editorial_approval_required"] is True
    assert manifest["fabricated_sources"] is False
    assert manifest["wordpress_write_performed"] is False
    assert (ROOT / "docs/V2200_INTELLIGENCE_PUBLISHING_STORY_MAP_STUDIO.md").exists()
