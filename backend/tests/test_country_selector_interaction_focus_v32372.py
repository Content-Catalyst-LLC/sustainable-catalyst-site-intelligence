from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_country_selector_focus_is_not_stolen_by_same_route_truth_updates():
    script = (ROOT / "backend/public_app/assets/browser-reliability-v3235.js").read_text()
    assert "function userControlFocused()" in script
    assert "select,input,textarea" in script
    assert "let lastRoute=''" in script
    assert "if(!next||next===lastRoute)return" in script
    assert "if(userControlFocused())return" in script
    assert "scsi:route-transition-end" in script


def test_country_selector_uses_native_browser_scrolling_contract():
    css = (ROOT / "backend/public_app/assets/app.css").read_text()
    assert "#countrySelect{touch-action:auto;overscroll-behavior:auto;scroll-behavior:auto}" in css


def test_wordpress_and_backend_browser_reliability_assets_match():
    backend = (ROOT / "backend/public_app/assets/browser-reliability-v3235.js").read_bytes()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js").read_bytes()
    assert backend == plugin


def test_browser_reliability_contract_declares_selector_focus_safety():
    import json
    policy = json.loads((ROOT / "backend/data/browser_reliability_policy_v3235.json").read_text())
    assert policy["accessibility"]["form_control_focus_protection"] is True
    assert policy["accessibility"]["native_select_scroll_preserved"] is True
    assert policy["accessibility"]["route_focus_only_on_route_change"] is True
    assert policy["reliability"]["repeated_workspace_state_does_not_refocus"] is True
