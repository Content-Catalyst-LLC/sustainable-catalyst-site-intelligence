from pathlib import Path

from app.homepage_summary_v4390 import build_homepage_summary
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _metrics(payload):
    return {item["id"]: item["value"] for item in payload["metrics"]}


def test_v44001_release_identity():
    assert APP_VERSION == "4.40.0.1"
    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == "4.40.0.1"
    assert RELEASE_NAME == "Homepage Live Intelligence Runtime Repair"


def test_homepage_summary_uses_runtime_feed_counts_and_bounded_signal_count():
    signals = [
        {"signal_id": f"signal-{i}", "label": f"Signal {i}", "value": str(i), "source_name": "Test"}
        for i in range(4)
    ]
    payload = {"signals": signals, "generated_at": "2026-09-12T05:00:00+00:00", "gateway": {"represented_source_count": 3}}
    summary = build_homepage_summary(payload, registered_source_count=11, enabled_source_count=7)
    assert _metrics(summary) == {
        "country_profiles": 172,
        "registered_sources": 11,
        "enabled_sources": 7,
        "current_signals": 4,
    }
    assert summary["represented_source_count"] == 3
    assert len(summary["highlights"]) == 4


def test_homepage_summary_preserves_zero_counts_without_unavailable_semantics():
    summary = build_homepage_summary({"signals": [], "gateway": {}}, registered_source_count=0, enabled_source_count=0)
    values = _metrics(summary)
    assert values["registered_sources"] == 0
    assert values["enabled_sources"] == 0
    assert values["current_signals"] == 0


def test_wordpress_runtime_repair_contract_is_present():
    root = Path(__file__).resolve().parents[2]
    plugin = root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    php = (plugin / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
    js = (plugin / "assets" / "sc-site-intelligence.js").read_text(encoding="utf-8")
    css = (plugin / "assets" / "sc-site-intelligence.css").read_text(encoding="utf-8")

    assert "Version: 4.40.0.1" in php
    assert "site-intelligence-v4.40.0.1" in php
    assert "data-status-endpoint" in php

    assert "configureTickerTrack" in js
    assert "--scsi-live-travel" in js
    assert "ResizeObserver" in js
    assert "metrics.registered_sources || metrics.live_feeds" in js
    assert "liveStatus.available_feeds.length" in js
    assert "liveStatus.default_feeds.length" in js
    assert "payload.featured_signal_count" in js

    assert 'data-scsi-ticker-ready="1"' in css
    assert "translate3d(var(--scsi-live-travel),0,0)" in css
