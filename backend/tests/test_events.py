from app.events import event_diagnostics, page_opportunities
from app.metrics import build_page_metrics
from app.registry import ContentRegistry
from app.sample_data import sample_event_rows, sample_page_rows


def test_event_diagnostics_reports_active_sample_events():
    registry = ContentRegistry("data/site_registry.seed.json")
    metrics = build_page_metrics(sample_page_rows(), sample_event_rows(), registry)
    diagnostics = event_diagnostics(sample_event_rows(), metrics)
    assert diagnostics["tracked_events_total"] >= 7
    assert diagnostics["tracked_events_active"] >= 5
    assert diagnostics["readiness"]["score"] > 40
    events = {item["event_name"]: item for item in diagnostics["events"]}
    assert events["sc_repository_click"]["event_count"] > 0
    assert events["sc_workbench_open"]["event_count"] > 0


def test_page_opportunities_returns_actionable_items():
    registry = ContentRegistry("data/site_registry.seed.json")
    metrics = build_page_metrics(sample_page_rows(), [], registry)
    opportunities = page_opportunities(metrics, limit=5)
    assert opportunities
    assert "actions" in opportunities[0]
