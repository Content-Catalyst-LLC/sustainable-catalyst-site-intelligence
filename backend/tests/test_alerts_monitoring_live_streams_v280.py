from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app import alerts_monitoring_live_streams as module

client = TestClient(app)


def settings(**overrides):
    base = {
        "alerts_monitoring_enabled": True,
        "alerts_stream_reconnect_seconds": 30,
        "alerts_stream_max_signals": 180,
        "alerts_stale_source_hours": 72,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def fake_collectors():
    return {
        "conditions": lambda _s, _l: {
            "state": "connected",
            "signals": [
                {
                    "id": "quake-1",
                    "title": "Earthquake public record",
                    "source_id": "usgs",
                    "record_type": "earthquake",
                    "observed_at": "2026-07-15T20:00:00Z",
                    "countries": ["KEN"],
                    "value_number": 6.1,
                    "unit": "magnitude",
                    "freshness_status": "live",
                    "source_url": "https://example.org/quake",
                }
            ],
        },
        "humanitarian": lambda _s, _l: {
            "state": "connected",
            "records": [
                {
                    "id": "report-1",
                    "title": "Displacement situation update",
                    "source_id": "reliefweb",
                    "category": "displacement",
                    "date": "2026-07-14",
                    "countries": ["KEN"],
                }
            ],
        },
        "economics": lambda _s, _l: {
            "integration": {"state": "connected"},
            "records": [
                {
                    "id": "inflation-1",
                    "indicator_name": "Consumer price inflation",
                    "source_id": "world-bank",
                    "record_type": "official_statistic",
                    "period": "2025",
                    "geography_code": "KEN",
                    "value_number": 5.2,
                    "unit": "percent",
                }
            ],
        },
        "law": lambda _s, _l: {"integration": {"state": "unavailable"}, "records": []},
        "science": lambda _s, _l: {"integration": {"state": "unavailable"}, "records": []},
        "resources": lambda _s, _l: {"integration": {"state": "unavailable"}, "records": []},
    }


def test_stream_snapshot_preserves_sources_and_no_fabrication(monkeypatch):
    monkeypatch.setattr(module, "_collectors", fake_collectors)
    payload = module.build_stream_snapshot(settings(), country="KEN", limit=20)
    assert payload["count"] == 3
    assert payload["fallback_used"] is False
    assert payload["credential_exposed"] is False
    assert payload["operational_emergency_alert"] is False
    assert {row["source_id"] for row in payload["signals"]} == {"usgs", "reliefweb", "world-bank"}


def test_browser_rules_are_stateless_and_thresholds_are_explicit(monkeypatch):
    monkeypatch.setattr(module, "_collectors", fake_collectors)
    rules = [
        {"id": "r1", "name": "Large earthquakes", "family": "conditions", "country": "KEN", "threshold_operator": "gte", "threshold_value": 6, "active": True},
        {"id": "r2", "name": "Displacement", "family": "humanitarian", "keyword": "displacement", "active": True},
    ]
    payload = module.evaluate_alert_rules(settings(), rules=rules)
    assert payload["match_count"] == 2
    assert payload["rules_persisted_server_side"] is False
    assert payload["automated_decision"] is False
    assert payload["operational_emergency_alert"] is False


def test_source_watch_and_digest(monkeypatch):
    monkeypatch.setattr(module, "_collectors", fake_collectors)
    watch = module.build_source_watch(settings(stale_source_hours=24), limit=20)
    assert watch["count"] >= 6
    assert any(item["source_id"] == "usgs" for item in watch["sources"])
    digest = module.build_monitoring_digest(settings(), rules=[{"name": "Kenya", "country": "KEN"}], country="KEN", limit=20)
    assert digest["summary"]["signals"] == 3
    assert digest["methodology"]["ai_generated"] is False
    assert digest["methodology"]["composite_risk_score"] is False


def test_sse_snapshot_is_reconnectable_and_bounded(monkeypatch):
    monkeypatch.setattr(module, "_collectors", fake_collectors)
    text = module.build_sse_snapshot(settings(), country="KEN", limit=20)
    assert "retry: 30000" in text
    assert "event: snapshot" in text
    assert "event: heartbeat" in text
    assert '"operational_emergency_alert":false' in text


def test_public_routes(monkeypatch):
    monkeypatch.setattr(module, "_collectors", fake_collectors)
    from app.config import get_settings
    get_settings.cache_clear()
    assert client.get("/public/alerts-monitoring").status_code == 200
    assert client.get("/public/live-intelligence-stream?country=KEN&limit=20").status_code == 200
    sse = client.get("/public/live-intelligence-stream/events?country=KEN&limit=20")
    assert sse.status_code == 200 and "text/event-stream" in sse.headers["content-type"]
    assert client.get("/public/alerts-monitoring/facets?limit=20").status_code == 200
    assert client.get("/public/alerts-monitoring/sources?limit=20").status_code == 200
    evaluated = client.post("/public/alerts-monitoring/evaluate", json={"rules": [{"name": "Kenya", "country": "KEN"}]})
    assert evaluated.status_code == 200 and evaluated.json()["match_count"] == 3
    digest = client.post("/public/alerts-monitoring/digest", json={"rules": [], "country": "KEN", "limit": 20})
    assert digest.status_code == 200
    assert client.get("/public/alerts-monitoring/diagnostics").status_code == 200


def test_interface_wordpress_and_release_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / "backend/public_app/index.html").read_text()
    js = (root / "backend/public_app/assets/alerts-v280.js").read_text()
    css = (root / "backend/public_app/assets/alerts-v280.css").read_text()
    app_js = (root / "backend/public_app/assets/app.js").read_text()
    php = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert 'data-route="alerts"' in html and 'id="alertsStudio"' in html
    assert "SCAlertsV280" in js and ".alerts-studio" in css
    assert 'const APP_VERSION="3.7.2"' in app_js
    assert "Version: 3.7.2" in php and "sc_alerts_monitoring_live_intelligence" in php
    assert "No server-side user tracking" in html
