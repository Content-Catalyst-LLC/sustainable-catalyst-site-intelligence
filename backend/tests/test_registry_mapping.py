from app.metrics import build_page_metrics, mapping_coverage, unmapped_suggestions
from app.models import GA4ReportRow
from app.registry import ContentRegistry


def test_registry_infers_publications_and_legal_pages():
    registry = ContentRegistry("data/site_registry.seed.json")
    pub = registry.resolve("/publications/", "Publications - Sustainable Catalyst")
    assert pub.status == "explicit"
    assert pub.item.hub == "Publications"
    legal = registry.resolve(
        "/war-crimes-crimes-against-humanity-genocide-and-the-architecture-of-international-criminal-law/",
        "War Crimes, Crimes Against Humanity, Genocide, and the Architecture of International Criminal Law",
    )
    assert legal.status in {"explicit", "inferred"}
    assert legal.item.article_map == "International Law"


def test_mapping_coverage_reports_unmapped_and_inferred_pages():
    registry = ContentRegistry("data/site_registry.seed.json")
    rows = [
        GA4ReportRow(dimensions={"pagePath": "/publications/", "pageTitle": "Publications"}, metrics={"screenPageViews": 10, "activeUsers": 5, "eventCount": 5, "engagementRate": 0.5, "averageSessionDuration": 100}),
        GA4ReportRow(dimensions={"pagePath": "/new-unknown-page/", "pageTitle": "New Unknown Page"}, metrics={"screenPageViews": 20, "activeUsers": 10, "eventCount": 2, "engagementRate": 0.4, "averageSessionDuration": 40}),
        GA4ReportRow(dimensions={"pagePath": "/new-linear-algebra-note/", "pageTitle": "Linear Algebra Note"}, metrics={"screenPageViews": 30, "activeUsers": 12, "eventCount": 8, "engagementRate": 0.6, "averageSessionDuration": 120}),
    ]
    metrics = build_page_metrics(rows, [], registry)
    coverage = mapping_coverage(metrics)
    assert coverage["total_pages"] == 3
    assert coverage["explicit_pages"] >= 1
    assert coverage["unmapped_pages"] >= 1
    assert coverage["inferred_pages"] >= 1
    suggestions = unmapped_suggestions(metrics, registry, limit=10)
    assert suggestions
