from app.metrics import build_page_metrics, dashboard_totals, hub_summary
from app.registry import ContentRegistry
from app.sample_data import sample_event_rows, sample_page_rows


def test_dashboard_metrics_build_from_sample_data():
    registry = ContentRegistry("data/site_registry.seed.json")
    metrics = build_page_metrics(sample_page_rows(), sample_event_rows(), registry)
    assert len(metrics) >= 5
    assert metrics[0].institutional_depth_score >= 0
    totals = dashboard_totals(metrics)
    assert totals["screen_page_views"] > 0
    assert totals["pathway_events"] > 0


def test_hub_summary_groups_pages():
    registry = ContentRegistry("data/site_registry.seed.json")
    metrics = build_page_metrics(sample_page_rows(), sample_event_rows(), registry)
    hubs = hub_summary(metrics)
    names = {row["hub"] for row in hubs}
    assert "Research" in names
    assert "Platform" in names
