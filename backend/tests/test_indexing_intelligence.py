from app.config import Settings
from app.ga4_client import GA4Client
from app.indexing_intelligence import SitemapFetcher, indexing_intelligence, parse_sitemap_xml, sitemap_report
from app.registry import ContentRegistry
from app.search_console import SearchConsoleClient


def test_parse_urlset_sitemap_xml():
    xml = '''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://sustainablecatalyst.com/research-library/</loc></url></urlset>'''
    kind, locs = parse_sitemap_xml(xml)
    assert kind == "urlset"
    assert locs == ["https://sustainablecatalyst.com/research-library/"]


def test_sitemap_fetcher_sample_fallback():
    settings = Settings(demo_mode=True, sitemap_live=False)
    report = SitemapFetcher(settings).fetch()
    assert report["ok"] is True
    assert report["source"] == "sample-sitemap"
    assert report["total_urls"] >= 3


def test_sitemap_report_maps_sample_urls():
    settings = Settings(demo_mode=True, sitemap_live=False)
    registry = ContentRegistry("backend/data/site_registry.seed.json")
    report = sitemap_report(settings, registry)
    assert report["ok"] is True
    assert report["total_urls"] >= report["mapped_urls"]
    assert "mapping_rate" in report


def test_indexing_intelligence_combines_sources():
    settings = Settings(demo_mode=True, sitemap_live=False, search_console_live=False)
    registry = ContentRegistry("backend/data/site_registry.seed.json")
    ga4 = GA4Client(settings)
    search = SearchConsoleClient(settings)
    report = indexing_intelligence(settings, registry, ga4, search)
    assert report["ok"] is True
    assert report["totals"]["total_paths"] >= 1
    assert report["coverage_rows"]
    assert "recommendations" in report
