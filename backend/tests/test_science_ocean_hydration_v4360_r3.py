from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ocean_runtime_exposes_explicit_hydration_state_and_ready_event():
    js=(ROOT/"backend/public_app/assets/ocean-observation-v4360.js").read_text(encoding="utf-8")
    assert 'dataset.oceanHydrationState="loading"' in js
    assert 'dataset.oceanHydrationState="ready"' in js
    assert 'dataset.oceanHydrationState="error"' in js
    assert 'scsi:ocean-observation-ready' in js
    assert 'cardCount=qa("[data-ocean-card]").length' in js


def test_science_ocean_launcher_awaits_ocean_open_and_reports_ready_catalog():
    js=(ROOT/"backend/public_app/assets/science-v240.js").read_text(encoding="utf-8")
    assert 'const opened=await window.SCSIOceanObservationV4360?.open?.()' in js
    assert 'panel?.dataset.oceanHydrationState==="ready"' in js
    assert 'cards===11' in js
    assert '11 marine systems available' in js


def test_r3_browser_gate_waits_for_hydration_not_just_panel_visibility():
    script=(ROOT/"scripts/browser_science_ocean_hydration_v4360_r3.py").read_text(encoding="utf-8")
    assert "dataset.oceanHydrationState === 'ready'" in script
    assert "[data-ocean-card]" in script
    assert 'ocean["hydration"] == "ready"' in script


def test_r3_ocean_and_science_assets_are_mirrored_to_wordpress():
    for name in ("ocean-observation-v4360.js","science-v240.js"):
        assert (ROOT/"backend/public_app/assets"/name).read_bytes()==(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/assets"/name).read_bytes()


def test_r3_assets_have_repair_specific_cache_bust_and_service_worker_namespace():
    index=(ROOT/"backend/public_app/index.html").read_text(encoding="utf-8")
    sw=(ROOT/"backend/public_app/service-worker.js").read_text(encoding="utf-8")
    assert '/app/assets/science-v240.js?v=4.36.0-r3' in index
    assert '/app/assets/ocean-observation-v4360.js?v=4.36.0-r3' in index
    assert 'const REPAIR="r3"' in sw
    assert 'v${RELEASE}-${REPAIR}' in sw
