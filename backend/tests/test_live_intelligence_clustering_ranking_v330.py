from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.live_intelligence_clustering_v330 import (
    SCHEMA_VERSION,
    cluster_event_records,
    ranking_policy,
    score_signal,
    select_ranked_signals,
)
from app.live_intelligence_v314 import build_live_intelligence
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc)


def _event(identifier: str, source: str, title: str, hours_ago: int, coordinates=None, country="USA", category="wildfire"):
    observed = (NOW - timedelta(hours=hours_ago)).isoformat()
    return {
        "id": identifier,
        "source_event_id": identifier,
        "title": title,
        "summary": title,
        "category": category,
        "source": source.lower().replace(" ", "-"),
        "source_name": source,
        "source_url": f"https://example.org/{identifier}",
        "observed_at": observed,
        "updated_at": observed,
        "coordinates": coordinates,
        "country_code": country,
        "severity": "high",
        "confidence": 0.9,
        "data_state": "live",
        "metadata": {},
    }


def test_nearby_cross_source_reports_cluster_with_traceable_members():
    records = [
        _event("a", "NASA EONET", "Wildfire near Northern California", 2, [-121.2, 39.1]),
        _event("b", "ReliefWeb", "Northern California wildfire situation update", 4, [-121.0, 39.0]),
    ]
    clusters, summary = cluster_event_records(records)
    assert len(clusters) == 1
    assert summary["duplicates_suppressed"] == 1
    assert summary["multi_source_clusters"] == 1
    assert clusters[0]["cluster_source_count"] == 2
    assert set(clusters[0]["corroborating_sources"]) == {"NASA EONET", "ReliefWeb"}
    assert set(clusters[0]["cluster_member_ids"]) == {"a", "b"}
    assert clusters[0]["cluster_id"].startswith("sc:cluster:")


def test_broadly_similar_events_are_not_merged_without_event_alignment():
    records = [
        _event("a", "NASA EONET", "Wildfire near Northern California", 2, [-121.2, 39.1]),
        _event("b", "NASA EONET", "Wildfire in southern Greece", 3, [23.7, 37.9], country="GRC"),
    ]
    clusters, summary = cluster_event_records(records)
    assert len(clusters) == 2
    assert summary["duplicates_suppressed"] == 0


def test_ranking_is_explainable_and_stale_data_is_penalized():
    base = {
        "signal_id": "event.test",
        "category": "earth_systems",
        "severity": "high",
        "status": "current",
        "data_state": "live",
        "observed_at": (NOW - timedelta(hours=2)).isoformat(),
        "source_priority": 10,
        "priority": 8,
        "cluster_source_count": 3,
    }
    live = score_signal(base, now=NOW)
    stale = score_signal({**base, "data_state": "stale"}, now=NOW)
    assert live["score"] > stale["score"]
    assert "3 represented sources" in live["reasons"]
    assert live["components"]["corroboration"] > 0
    assert stale["components"]["state_penalty"] < 0


def test_ranked_selection_retains_category_diversity_and_rank_fields():
    signals = []
    for index, category in enumerate(["earth_systems", "human_systems", "research", "economy_resources"]):
        signals.append({
            "signal_id": f"signal.{index}",
            "category": category,
            "source_name": f"Source {index}",
            "feed_id": f"feed_{index}",
            "severity": "informational",
            "data_state": "live",
            "observed_at": (NOW - timedelta(hours=index + 1)).isoformat(),
            "source_priority": 30,
            "priority": 30 + index,
        })
    selected = select_ranked_signals(signals, 4, now=NOW)
    assert {item["category"] for item in selected} == {"earth_systems", "human_systems", "research", "economy_resources"}
    assert [item["selection_rank"] for item in selected] == [1, 2, 3, 4]
    assert all(item["selection_reasons"] for item in selected)
    assert all("ranking_components" in item for item in selected)


def test_live_feed_exposes_cluster_and_ranking_transparency(tmp_path):
    duplicate_records = [
        _event("eq-a", "USGS Earthquake Hazards Program", "M 5.6 earthquake near Test Coast", 2, [-122.0, 40.0], category="earthquake"),
        _event("eq-b", "Partner public source", "M5.6 earthquake near Test Coast", 3, [-122.1, 40.1], category="earthquake"),
    ]
    payload = {
        "events": duplicate_records,
        "delivery_state": "live",
        "generated_at": NOW.isoformat(),
        "source_states": {"usgs": "live", "partner": "live"},
    }
    settings = Settings(
        version="3.21.0",
        external_live=True,
        public_connector_live_checks=False,
        live_source_operations_enabled=False,
    )
    with patch("app.live_intelligence_v314.unified_events", return_value=payload):
        result = build_live_intelligence(settings, feeds="usgs_earthquakes", limit=4)
    event = next(item for item in result["signals"] if item["signal_id"].startswith("event."))
    assert event["cluster_source_count"] == 2
    assert event["selection_score"] >= 0
    assert event["selection_reasons"]
    assert event["development_state"] in {"new", "developing", "stable", "continuing"}
    clustering = result["feed_state"]["events"]["clustering"]
    assert clustering["duplicates_suppressed"] == 1
    assert result["feed_state"]["ranking"]["policy_url"] == "/public/live-intelligence/ranking-policy"
    assert result["display"]["transparent_ranking_supported"] is True


def test_public_ranking_policy_endpoint_is_explicit_about_boundaries():
    direct = ranking_policy()
    assert direct["schema"] == SCHEMA_VERSION
    assert direct["ranking"]["selection_reasons_returned_per_signal"] is True
    assert any("not measure truth" in item for item in direct["boundaries"])
    response = TestClient(app).get("/public/live-intelligence/ranking-policy")
    assert response.status_code == 200
    assert response.json()["schema"] == SCHEMA_VERSION


def test_wordpress_ticker_exposes_multi_source_and_selection_context():
    js = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    assert "cluster_source_count" in js
    assert "selection_reasons" in js
    assert "Selected because:" in js
    assert "development_state" in js
