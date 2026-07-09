from app.config import Settings
from app.ga4_client import GA4Client
from app.publishing_intelligence import publishing_intelligence, page_strategy_rows, article_map_performance
from app.registry import ContentRegistry
from app.search_console import SearchConsoleClient


def test_publishing_intelligence_sample_data():
    settings = Settings(demo_mode=True, registry_path="data/site_registry.seed.json", search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    report = publishing_intelligence(GA4Client(settings), SearchConsoleClient(settings), registry, limit=10)
    assert report["ok"] is True
    assert report["totals"]["priority_pages"] >= 1
    assert report["publishing_queue"]
    assert report["article_map_performance"]
    assert "methodology" in report


def test_article_map_performance_groups_rows():
    rows = [
        {"hub": "Research", "article_map": "Linear Algebra", "current_views": 100, "prior_views": 50, "search_impressions": 200, "repository_clicks": 5, "workbench_events": 2, "research_librarian_events": 1, "pathway_events": 7, "strategy_score": 60, "title": "A", "path": "/a/", "status": "rising"},
        {"hub": "Research", "article_map": "Linear Algebra", "current_views": 50, "prior_views": 100, "search_impressions": 75, "repository_clicks": 0, "workbench_events": 0, "research_librarian_events": 0, "pathway_events": 1, "strategy_score": 30, "title": "B", "path": "/b/", "status": "decay"},
    ]
    grouped = article_map_performance(rows)
    assert grouped[0]["name"] == "Linear Algebra"
    assert grouped[0]["pages"] == 2
    assert grouped[0]["current_views"] == 150
    assert grouped[0]["views_growth_rate"] == 0.0
