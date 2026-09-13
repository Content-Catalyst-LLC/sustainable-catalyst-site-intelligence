from pathlib import Path

from app.version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _assets():
    root = Path(__file__).resolve().parents[2]
    plugin = root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    return (
        (plugin / "assets" / "sc-site-intelligence.js").read_text(encoding="utf-8"),
        (plugin / "assets" / "sc-site-intelligence.css").read_text(encoding="utf-8"),
        (plugin / "sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8"),
    )


def test_v44003_release_identity():
    assert APP_VERSION == "4.40.0.3"
    assert EXPECTED_WORDPRESS_PLUGIN_VERSION == APP_VERSION
    assert RELEASE_NAME == "Live Intelligence Ticker Pace & Readability Repair"


def test_ticker_uses_distance_based_readable_pace():
    js, css, php = _assets()
    assert "Version: 4.40.0.3" in php
    assert "site-intelligence-v4.40.0.3" in php
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
    ]:
        assert marker in js
    assert "--scsi-live-duration:42s;" not in css
    assert "--scsi-live-mobile-duration:36s;" not in css
    assert "--scsi-live-duration:96s;" in css
    assert "--scsi-live-mobile-duration:118s;" in css


def test_pace_repair_preserves_ticker_accessibility_and_geometry():
    js, css, _ = _assets()
    for marker in [
        "configureTickerTrack",
        "Math.ceil(primarySet.getBoundingClientRect().width)",
        "aria-hidden=\"true\" inert",
        "control.tabIndex = -1",
        "root.classList.contains('is-focus-paused')",
        "root.classList.contains('is-hover-paused')",
        "reducedMotion.matches",
    ]:
        assert marker in js
    assert 'data-scsi-ticker-ready="1"' in css
    assert "translate3d(var(--scsi-live-travel),0,0)" in css
    assert "animation-play-state:paused!important" in css
