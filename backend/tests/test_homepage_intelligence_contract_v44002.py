from pathlib import Path

from app.homepage_summary_v4390 import build_homepage_summary
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _metrics(payload):
    return {item["id"]: item["value"] for item in payload["metrics"]}


def test_v44002_release_identity():
    assert APP_VERSION == "4.40.0.2"
    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
    assert RELEASE_NAME == "Homepage Intelligence Contract & Ticker Recovery"


def test_homepage_capability_contract_is_restored():
    signals = [
        {"signal_id": f"signal-{i}", "label": f"Signal {i}", "value": str(i), "source_name": "Test"}
        for i in range(4)
    ]
    summary = build_homepage_summary(
        {"signals": signals, "generated_at": "2026-09-12T05:00:00+00:00", "gateway": {"represented_source_count": 3}},
        live_feed_count=8,
    )
    assert _metrics(summary) == {
        "country_profiles": 172,
        "enabled_connectors": 14,
        "public_workspaces": 35,
        "live_feeds": 8,
    }
    assert summary["featured_signal_count"] == 4
    assert summary["represented_source_count"] == 3
    assert len(summary["highlights"]) == 4


def test_homepage_markup_embeds_live_ticker_and_correct_slots():
    root = Path(__file__).resolve().parents[2]
    plugin = root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    php = (plugin / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (plugin / "assets" / "sc-site-intelligence.js").read_text(encoding="utf-8")
    css = (plugin / "assets" / "sc-site-intelligence.css").read_text(encoding="utf-8")

    assert "Version: 4.40.0.2" in php
    assert "site-intelligence-v4.40.0.2" in php
    for marker in ["enabled_connectors", "public_workspaces", "live_feeds", "data-home-live-ticker"]:
        assert marker in php
    assert "'surface' => 'homepage'" in php
    assert "'presentation' => 'ticker'" in php

    for marker in [
        "renderMetric('country_profiles', metrics.country_profiles)",
        "renderMetric('enabled_connectors', metrics.enabled_connectors)",
        "renderMetric('public_workspaces', metrics.public_workspaces)",
        "renderMetric('live_feeds', metrics.live_feeds)",
        "configureTickerTrack",
        "setupLiveIntelligence();",
    ]:
        assert marker in js
    assert "liveStatus.available_feeds.length" not in js
    assert "liveStatus.default_feeds.length" not in js
    assert "scsi-home-summary__live-ticker" in css
