"""Static certification gates for v4.57.5 Ocean Surface frontend integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "web/app/assets/ocean-surface-visualization-v4575.js"


def test_ocean_surface_visualization_asset_exists():
    script = ASSET.read_text()
    assert 'window.addEventListener("scsi:ocean-surface-enter",mount)' in script
    assert 'ocean4575Map' in script
    assert 'ocean4575Chart' in script


def test_source_truth_guardrails():
    script = ASSET.read_text()
    assert '/public/ocean-intelligence/observation/normalize' in script
    assert 'network-verified' in script
    assert 'No source-attributed observations imported' in script
    assert 'max-min||1' in script
    assert 'evidence classes are not connected' in script


def test_both_frontends_register_v4575():
    for page in ('web/index.html', 'web/app/index.html'):
        html = (ROOT / page).read_text()
        assert '/app/assets/ocean-surface-visualization-v4575.js?v=4.57.6' in html
