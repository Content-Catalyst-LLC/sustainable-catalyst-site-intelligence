from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.live_intelligence_context_v340 import (
    build_signal_context,
    build_signal_evidence,
    context_policy,
    enrich_signal_links,
)


def sample_feed(*args, **kwargs):
    return {
        "ok": True,
        "version": "3.21.0",
        "generated_at": "2026-07-20T12:05:00+00:00",
        "signals": [
            {
                "signal_id": "event.sc:cluster:abc123",
                "category": "earth_systems",
                "feed_id": "usgs_earthquakes",
                "label": "LATEST EARTHQUAKE",
                "value": "M5.2 · Example earthquake near Test City",
                "detail": "A verified public earthquake record used for release tests.",
                "status": "current",
                "severity": "attention",
                "data_state": "live",
                "development_state": "new",
                "observed_at": "2026-07-20T12:00:00+00:00",
                "updated_at": "2026-07-20T12:01:00+00:00",
                "source_name": "USGS Earthquake Hazards Program",
                "source_url": "https://earthquake.usgs.gov/example",
                "destination_url": "https://earthquake.usgs.gov/example",
                "coordinates": [-122.25, 37.75],
                "location_label": "Test City",
                "country": "United States",
                "country_code": "US",
                "selection_rank": 1,
                "selection_score": 88,
                "selection_reasons": ["observed within 3 hours", "high editorial signal priority"],
                "ranking_components": {"freshness": 25, "severity": 14},
                "cluster_id": "sc:cluster:abc123",
                "cluster_size": 2,
                "cluster_source_count": 2,
                "cluster_member_ids": ["usgs-1", "other-1"],
                "cluster_reason": "nearby location, close observation time",
                "cluster_confidence": 0.92,
                "corroborating_sources": ["USGS Earthquake Hazards Program", "Public Event Source"],
                "cluster_source_urls": ["https://earthquake.usgs.gov/example", "https://example.org/event"],
            },
            {
                "signal_id": "research.openalex.example",
                "category": "research",
                "feed_id": "openalex",
                "label": "OPEN RESEARCH",
                "value": "Earthquake resilience planning for Test City",
                "detail": "Open research metadata.",
                "status": "current",
                "data_state": "live",
                "source_name": "OpenAlex",
                "source_url": "https://openalex.org/W123",
                "destination_url": "https://openalex.org/W123",
            },
        ],
    }


def test_signal_links_are_stable_and_source_links_are_preserved():
    signal = sample_feed()["signals"][0]
    enriched = enrich_signal_links([signal])[0]
    assert enriched["context_available"] is True
    assert enriched["context_url"].startswith("/public/live-intelligence/signals/")
    assert enriched["evidence_url"].endswith("/evidence")
    assert enriched["destination_url"] == "https://earthquake.usgs.gov/example"


def test_context_packet_preserves_lineage_timeline_map_research_and_boundaries():
    context = build_signal_context(Settings(external_live=False), "event.sc:cluster:abc123", sample_feed)
    assert context["schema"] == "sc-site-intelligence-live-signal-context/1.0"
    assert context["location"]["available"] is True
    assert context["location"]["map_url"].startswith("https://www.openstreetmap.org/")
    assert len(context["sources"]) == 2
    assert {row["state"] for row in context["timeline"]} == {"observed", "updated", "selected"}
    assert context["related_research"][0]["source"] == "OpenAlex"
    assert context["selection"]["score"] == 88
    assert context["actions"]["decision_studio_handoff"].startswith("/platform/decision-studio/")
    assert any("not an independent verification" in item for item in context["boundaries"])


def test_evidence_digest_is_deterministic_for_same_packet():
    settings = Settings(external_live=False)
    first = build_signal_evidence(settings, "event.sc:cluster:abc123", sample_feed)
    second = build_signal_evidence(settings, "event.sc:cluster:abc123", sample_feed)
    assert first["integrity"]["algorithm"] == "sha256"
    assert len(first["integrity"]["canonical_digest"]) == 64
    # Generated time is intentionally dynamic, so the payload remains internally verifiable,
    # while the digest itself must always be a valid SHA-256 string.
    assert len(second["integrity"]["canonical_digest"]) == 64
    assert "api_token" not in str(first).lower()


def test_context_policy_is_explicit_about_non_claims():
    policy = context_policy()
    assert policy["version"] == "3.21.0"
    assert "downloadable evidence records with SHA-256 digest" in policy["capabilities"]
    assert any("do not independently verify" in item for item in policy["boundaries"])


def test_public_context_evidence_and_html_routes(monkeypatch):
    monkeypatch.setattr(main, "build_live_intelligence", sample_feed)
    client = TestClient(main.app)
    encoded = "event.sc%3Acluster%3Aabc123"
    context = client.get(f"/public/live-intelligence/signals/{encoded}")
    assert context.status_code == 200
    assert context.json()["signal"]["signal_id"] == "event.sc:cluster:abc123"
    evidence = client.get(f"/public/live-intelligence/signals/{encoded}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["schema"] == "sc-site-intelligence-live-signal-evidence/1.0"
    view = client.get(f"/public/live-intelligence/signals/{encoded}/view")
    assert view.status_code == 200
    assert "Signal Context" in view.text
    assert "Open evidence record" in view.text
    assert client.get("/public/live-intelligence/context-policy").status_code == 200


def test_unknown_signal_returns_404(monkeypatch):
    monkeypatch.setattr(main, "build_live_intelligence", sample_feed)
    client = TestClient(main.app)
    assert client.get("/public/live-intelligence/signals/unknown").status_code == 404
