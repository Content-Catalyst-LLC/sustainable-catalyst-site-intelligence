from fastapi.testclient import TestClient

from app.main import app
from app.public_source_pages import public_source_navigation, public_source_page_templates, public_source_page_visual_qa

client = TestClient(app)


def test_public_source_navigation_marks_active_page():
    payload = public_source_navigation("source-health")
    assert payload["ok"] is True
    active = [item for item in payload["items"] if item["active"]]
    assert len(active) == 1
    assert active[0]["slug"] == "source-health"
    assert active[0]["path"] == "/platform/site-intelligence/source-health/"


def test_public_source_page_templates_include_canonical_paths_and_shortcodes():
    payload = public_source_page_templates()
    slugs = {item["slug"] for item in payload["templates"]}
    assert {"sources", "source-health", "indicators", "sustainability-indicators", "research-metadata", "publication-metadata", "repository-intelligence"}.issubset(slugs)
    template = [item for item in payload["templates"] if item["slug"] == "repository-intelligence"][0]
    assert template["canonical_path"] == "/platform/site-intelligence/repository-intelligence/"
    assert template["shortcode"] == "[sc_public_repository_intelligence]"
    assert "API credentials and tokens" in template["public_exclusions"]


def test_public_source_page_visual_qa_is_release_ready():
    payload = public_source_page_visual_qa()
    assert payload["ok"] is True
    assert payload["score"] == 100
    assert all(item["status"] == "pass" for item in payload["checks"])


def test_public_source_page_endpoints():
    for path in [
        "/public/source-pages",
        "/public/source-pages/navigation?current=indicators",
        "/public/source-pages/templates?slug=sources",
        "/public/source-pages/visual-qa",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["ok"] is True


def test_unknown_source_template_slug_404s():
    response = client.get("/public/source-pages/templates?slug=missing")
    assert response.status_code == 404
