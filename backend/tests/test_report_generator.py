from app.report_generator import site_intelligence_report, to_markdown, to_csv, bundle_report


def test_site_report_exports_markdown_and_csv():
    dashboard = {
        "source": "demo",
        "date_range": {"start_date": "28daysAgo", "end_date": "today"},
        "totals": {"screen_page_views": 1200, "active_users": 200, "avg_institutional_depth_score": 42},
        "mapping_coverage": {"mapping_coverage_rate": 81},
        "recommendations": ["Improve internal links."],
        "top_pages": [{"title": "A", "path": "/a/", "status": "covered"}],
        "unmapped_pages": [],
        "event_diagnostics": {"score": 50},
    }
    report = site_intelligence_report(dashboard)
    assert report["report_id"] == "site-intelligence"
    assert "Weekly Site Intelligence" in to_markdown(report)
    assert "report_id,title,section" in to_csv(report)


def test_bundle_report_contains_reports():
    report = site_intelligence_report({"source": "demo", "totals": {}, "mapping_coverage": {}})
    bundle = bundle_report([report])
    assert bundle["ok"] is True
    assert bundle["reports"][0]["report_id"] == "site-intelligence"
