from pathlib import Path

from app.homepage_summary_v4390 import build_homepage_summary
from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _plugin_assets():
    root = Path(__file__).resolve().parents[2]
    plugin = root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    return (
        (plugin / "assets" / "sc-site-intelligence.js").read_text(encoding="utf-8"),
        (plugin / "assets" / "sc-site-intelligence.css").read_text(encoding="utf-8"),
        (plugin / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8"),
    )


def test_v4410_release_identity_advances_without_regressing_homepage_contract():
    assert APP_VERSION == "4.41.0"
    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
    assert RELEASE_NAME == "Spatial & Global Energy Intelligence"

    signals = [
        {"signal_id": f"signal-{i}", "label": f"Signal {i}", "value": str(i), "source_name": "Test"}
        for i in range(4)
    ]
    summary = build_homepage_summary(
        {"signals": signals, "generated_at": "2026-09-13T06:00:00+00:00", "gateway": {"represented_source_count": 3}},
        live_feed_count=8,
    )
    metrics = {item["id"]: item["value"] for item in summary["metrics"]}
    assert metrics == {
        "country_profiles": 172,
        "enabled_connectors": 14,
        "public_workspaces": 35,
        "live_feeds": 8,
    }
    assert summary["featured_signal_count"] == 4
    assert summary["represented_source_count"] == 3


def test_v44003_distance_based_ticker_is_preserved_under_v4410_identity():
    js, css, php = _plugin_assets()
    assert "Version: 4.41.0" in php
    assert "site-intelligence-v4.41.0" in php

    for marker in [
        "const calculateTickerPace = function (travel)",
        "const targetPixelsPerSecond = mobileQuery.matches ? 23 : 28;",
        "const minimumDurationSeconds = mobileQuery.matches ? 90 : 75;",
        "const maximumDurationSeconds = mobileQuery.matches ? 260 : 220;",
        "const measuredDurationSeconds = travel / targetPixelsPerSecond;",
        "track.style.setProperty('--scsi-live-duration', durationValue)",
        "track.style.setProperty('--scsi-live-mobile-duration', durationValue)",
        "root.dataset.scsiTickerPixelsPerSecond",
        "root.dataset.scsiTickerDurationSeconds",
        "root.dataset.scsiTickerTravelPixels",
        "configureTickerTrack",
        "Math.ceil(primarySet.getBoundingClientRect().width)",
        "aria-hidden=\"true\" inert",
        "control.tabIndex = -1",
        "reducedMotion.matches",
    ]:
        assert marker in js

    assert "--scsi-live-duration:42s;" not in css
    assert "--scsi-live-mobile-duration:36s;" not in css
    assert "--scsi-live-duration:96s;" in css
    assert "--scsi-live-mobile-duration:118s;" in css
    assert 'data-scsi-ticker-ready="1"' in css
    assert "translate3d(var(--scsi-live-travel),0,0)" in css


def test_v4410_keeps_homepage_live_ticker_markup_and_metric_slots():
    js, css, php = _plugin_assets()
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
    assert "scsi-home-summary__live-ticker" in css
