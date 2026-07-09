from app.config import Settings
from app.ga4_client import GA4Client
from app.public_dashboard import build_public_dashboard, public_methodology, public_readiness_report
from app.registry import ContentRegistry


def test_public_dashboard_sanitizes_internal_metrics():
    settings = Settings(demo_mode=True, registry_path="data/site_registry.seed.json")
    registry = ContentRegistry(settings.registry_path)
    report = build_public_dashboard(GA4Client(settings), registry)
    assert report["ok"] is True
    assert report["mode"] == "public"
    assert "views_band" in report["summary"]
    assert "top_pages" not in report
    assert "unmapped_pages" not in report
    assert report["methodology"]["excluded"]


def test_public_methodology_documents_exclusions():
    methodology = public_methodology()
    assert methodology["ok"] is True
    assert any("Raw GA4" in item for item in methodology["excluded"])


def test_public_readiness_report_has_checks():
    settings = Settings(demo_mode=True, registry_path="data/site_registry.seed.json")
    registry = ContentRegistry(settings.registry_path)
    report = public_readiness_report(GA4Client(settings), registry)
    assert report["ok"] is True
    assert report["checks"]
    assert report["public_status"] in {"public_ready", "public_candidate", "internal_review", "not_public_ready"}
