from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.intelligence_publishing_v2200 import IntelligencePublishingStudio, SCHEMA_VERSION
from app.main import app


def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "publishing"
    return Settings(
        intelligence_publishing_root_path=str(root),
        intelligence_publishing_projects_path=str(root / "projects.jsonl"),
        intelligence_publishing_blocks_path=str(root / "blocks.jsonl"),
        intelligence_publishing_reviews_path=str(root / "reviews.jsonl"),
        intelligence_publishing_versions_path=str(root / "versions.jsonl"),
        intelligence_publishing_policy_path=str(Path(__file__).resolve().parents[1] / "data/intelligence_publishing_policy_v2200.json"),
    )


def build_publication(tmp_path: Path, visibility: str = "public"):
    center = IntelligencePublishingStudio(settings(tmp_path))
    project = center.create_project({
        "project_id": "pub:kenya-climate",
        "title": "Kenya Climate and Development Dossier",
        "summary": "A source-aware intelligence publication.",
        "visibility": "private",
        "authors": ["Sustainable Catalyst"],
        "source_ids": ["source:world-bank"],
        "evidence_ids": ["claim:kenya-climate"],
        "methodology_notes": ["Values retain source dates and units."],
        "limitations": ["Spatial proximity does not establish causation."],
    })["project"]
    center.add_block(project["project_id"], {"block_type": "heading", "title": "Context", "content": {"text": "Country and regional context."}, "position": 1})
    center.add_block(project["project_id"], {"block_type": "map", "title": "Observed layers", "content": {"text": "Map layers for public interpretation.", "layers": ["drought", "population"]}, "source_ids": ["source:nasa"], "position": 2})
    center.add_block(project["project_id"], {"block_type": "timeline", "title": "Change over time", "content": {"text": "A dated sequence of observations.", "events": [{"date": "2025-01-01", "label": "Observation"}]}, "evidence_ids": ["evidence:timeline"], "position": 3})
    center.add_block(project["project_id"], {"block_type": "evidence_table", "title": "Evidence", "content": {"text": "Approved evidence records."}, "evidence_ids": ["evidence:1"], "position": 4})
    center.submit_review(project["project_id"], {"reviewer_role": "editor"})
    center.decide_review(project["project_id"], {"decision": "approved", "reviewer_role": "editor", "human_review_confirmed": True})
    published = center.publish_project(project["project_id"], {"visibility": visibility, "human_publish_confirmed": True})
    return center, published


def test_publication_requires_human_editorial_approval(tmp_path):
    center = IntelligencePublishingStudio(settings(tmp_path))
    project = center.create_project({"project_id": "pub:test", "title": "Test"})["project"]
    center.add_block(project["project_id"], {"block_type": "narrative", "content": {"text": "Text"}})
    try:
        center.publish_project(project["project_id"], {"visibility": "public", "human_publish_confirmed": True})
        assert False
    except ValueError as exc:
        assert "approved human editorial review" in str(exc)


def test_evidence_blocks_require_references(tmp_path):
    center = IntelligencePublishingStudio(settings(tmp_path))
    project = center.create_project({"project_id": "pub:test", "title": "Test"})["project"]
    try:
        center.add_block(project["project_id"], {"block_type": "map", "content": {"text": "Map"}})
        assert False
    except ValueError as exc:
        assert "source_ids or evidence_ids" in str(exc)


def test_publication_versions_are_immutable_and_story_map_is_source_aware(tmp_path):
    center, published = build_publication(tmp_path)
    item = published["publication"]
    assert item["version_number"] == 1
    assert item["version_sha256"]
    story = center.story_map(item["publication_id"], public=True)
    assert story["map_block_count"] == 1
    assert story["timeline_block_count"] == 1
    assert "do not establish causation" in story["interpretation_boundary"]
    history = center.version_history(item["publication_id"], public=True)
    assert history["count"] == 1


def test_unlisted_publication_is_omitted_from_directory_but_resolvable(tmp_path):
    center, published = build_publication(tmp_path, visibility="unlisted")
    assert center.public_publications()["count"] == 0
    detail = center.publication_detail(published["publication"]["publication_id"], public=True)
    assert detail["visibility"] == "unlisted"


def test_exports_preserve_sources_evidence_and_print_html(tmp_path):
    center, published = build_publication(tmp_path)
    export = center.export_publication(published["publication"]["publication_id"], public=True)
    assert export["packet"]["packet_sha256"]
    assert export["packet"]["pdf_ready_html"] is True
    assert export["packet"]["pdf_binary_generated"] is False
    assert "source:nasa" in export["markdown"]
    assert "block_type" in export["csv"]
    assert "<article>" in export["html"]


def test_wordpress_handoff_is_read_only(tmp_path):
    center, published = build_publication(tmp_path)
    handoff = center.wordpress_handoff(published["publication"]["publication_id"])
    assert handoff["destination"] == "wordpress"
    assert handoff["read_only"] is True
    assert handoff["write_performed"] is False
    assert "sc_intelligence_publication" in handoff["suggested_shortcode"]


def test_public_and_admin_routes(tmp_path):
    cfg = settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: cfg
    try:
        client = TestClient(app)
        assert client.get("/public/intelligence-publishing").status_code == 200
        assert client.get("/public/intelligence-publishing/methodology").status_code == 200
        assert client.get("/admin/intelligence-publishing/control-center").status_code == 200
        project = client.post("/admin/intelligence-publishing/projects", json={"project_id": "pub:route", "title": "Route Publication"}).json()["project"]
        assert client.post(f"/admin/intelligence-publishing/projects/{project['project_id']}/blocks", json={"block_type": "narrative", "content": {"text": "Narrative"}}).status_code == 200
        assert client.post(f"/admin/intelligence-publishing/projects/{project['project_id']}/review/submit", json={}).status_code == 200
        assert client.post(f"/admin/intelligence-publishing/projects/{project['project_id']}/review/decide", json={"decision": "approved", "human_review_confirmed": True}).status_code == 200
        assert client.post(f"/admin/intelligence-publishing/projects/{project['project_id']}/publish", json={"visibility": "public", "human_publish_confirmed": True}).status_code == 200
        assert client.get("/public/intelligence-publications").json()["count"] == 1
        assert client.get(f"/public/intelligence-publications/{project['project_id']}").status_code == 200
        assert client.get(f"/public/intelligence-publications/{project['project_id']}/story-map").status_code == 200
        assert client.get(f"/public/intelligence-publications/{project['project_id']}/export").status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_public_summary_exposes_editorial_boundaries(tmp_path):
    summary = IntelligencePublishingStudio(settings(tmp_path)).public_summary()
    assert summary["schema"] == SCHEMA_VERSION
    assert summary["human_editorial_approval_required"] is True
    assert summary["automatic_publication"] is False
    assert any("causation" in x.lower() for x in summary["boundaries"])
