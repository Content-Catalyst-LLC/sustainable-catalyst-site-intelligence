from pathlib import Path

def test_public_interface_redesign_assets():
    root = Path(__file__).resolve().parents[2]
    js = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js").read_text()
    css = (root / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css").read_text()
    assert "renderCountryPublic" in js
    assert "renderCuratedDirectory" in js
    assert "No validated value" in js
    assert ".scsi-public-domain-grid" in css
    assert ".scsi-directory-grid" in css
