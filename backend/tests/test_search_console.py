from app.config import Settings
from app.registry import ContentRegistry
from app.search_console import SearchConsoleClient, resolve_date, opportunity_score


def test_search_client_sample_intelligence_shape():
    settings = Settings(search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    client = SearchConsoleClient(settings)
    data = client.search_intelligence(registry)
    assert data["ok"] is True
    assert data["source"] == "sample-search"
    assert data["totals"]["impressions"] > 0
    assert data["top_pages"]
    assert data["top_queries"]
    assert data["topic_momentum"]


def test_search_page_summary_maps_registry_status():
    settings = Settings(search_console_live=False)
    registry = ContentRegistry(settings.registry_path)
    client = SearchConsoleClient(settings)
    pages = client.page_summary(registry)
    assert pages
    assert all("opportunity_score" in page for page in pages)
    assert any(page["mapping_status"] in {"explicit", "inferred", "unmapped"} for page in pages)


def test_search_diagnostics_sample_mode():
    settings = Settings(search_console_live=False)
    client = SearchConsoleClient(settings)
    diagnostics = client.diagnostics()
    assert diagnostics["enabled"] is False
    assert diagnostics["request_ok"] is False


def test_resolve_date_relative():
    value = resolve_date("28daysAgo")
    assert len(value) == 10
    assert value.count("-") == 2


def test_opportunity_score_directional():
    high = opportunity_score(5000, 0.01, 11, mapped=True)
    low = opportunity_score(50, 0.12, 2, mapped=True)
    assert high > low
