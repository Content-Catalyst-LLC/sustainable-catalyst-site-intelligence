from pathlib import Path


def test_plugin_version_is_110():
    plugin = Path(__file__).resolve().parents[2] / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "sustainable-catalyst-site-intelligence.php"
    text = plugin.read_text()
    assert "Version: 1.14.0" in text
    assert "const VERSION = '1.14.0';" in text


def test_public_shortcode_visual_alignment_css_present():
    css = Path(__file__).resolve().parents[2] / "wordpress-plugin" / "sustainable-catalyst-site-intelligence" / "assets" / "sc-site-intelligence.css"
    text = css.read_text()
    assert "v1.10.0 Public Shortcode Visual Alignment" in text
    assert ".ccp-site-intelligence-public .ccp-live-shell > .scsi-public-dashboard" in text
    assert "--scsi-public-red: #9b1111" in text
    assert "border-top: 7px solid var(--scsi-public-black)" in text
