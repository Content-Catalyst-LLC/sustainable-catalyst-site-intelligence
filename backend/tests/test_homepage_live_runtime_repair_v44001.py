from pathlib import Path


def test_v44001_measured_ticker_repair_is_preserved():
    root = Path(__file__).resolve().parents[2]
    plugin = root / "wordpress-plugin" / "sustainable-catalyst-site-intelligence"
    js = (plugin / "assets" / "sc-site-intelligence.js").read_text(encoding="utf-8")
    css = (plugin / "assets" / "sc-site-intelligence.css").read_text(encoding="utf-8")
    assert "configureTickerTrack" in js
    assert "--scsi-live-travel" in js
    assert "ResizeObserver" in js
    assert 'data-scsi-ticker-ready="1"' in css
    assert "translate3d(var(--scsi-live-travel),0,0)" in css
    assert "translateX(-50%)" not in css
