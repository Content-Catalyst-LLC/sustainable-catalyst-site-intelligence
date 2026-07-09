from app.config import Settings
from app.registry import ContentRegistry
from app.search_console import SearchConsoleClient
from app.seo_intelligence import internal_link_review, metadata_review, seo_recommendations, overlap_ratio, title_status


def test_title_status_flags_generic_archive_titles():
    result = title_status("Mathematical Modeling Archives - Sustainable Catalyst")
    assert result["status"] in {"review", "priority"}
    assert result["issues"]


def test_query_title_overlap_directional():
    assert overlap_ratio("Linear Algebra for Systems Modeling", "linear algebra systems modeling") > 0.5
    assert overlap_ratio("Publications", "climate energy intelligence dashboard") < 0.5


def test_metadata_review_sample_shape():
    settings = Settings(search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    client = SearchConsoleClient(settings)
    data = metadata_review(client, registry)
    assert data["ok"] is True
    assert data["source"] == "sample-search"
    assert data["metadata_reviews"]
    assert "metadata_priority_score" in data["metadata_reviews"][0]
    assert data["summary"]["pages_reviewed"] > 0


def test_internal_link_review_sample_shape():
    settings = Settings(search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    client = SearchConsoleClient(settings)
    data = internal_link_review(client, registry)
    assert data["ok"] is True
    assert data["internal_link_opportunities"]
    assert "anchor_suggestions" in data["internal_link_opportunities"][0]
    assert data["summary"]["pages_reviewed"] > 0


def test_seo_recommendations_combined_shape():
    settings = Settings(search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    client = SearchConsoleClient(settings)
    data = seo_recommendations(client, registry)
    assert data["ok"] is True
    assert data["top_recommendations"]
    assert "priority_score" in data["top_recommendations"][0]
