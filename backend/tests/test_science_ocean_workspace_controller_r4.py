from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT/path).read_text(encoding="utf-8")


def test_main_router_cache_busts_and_recovers_science_controller():
    index=text("backend/public_app/index.html")
    app=text("backend/public_app/assets/app.js")
    assert '/app/assets/app.js?v=4.37.0' in index
    assert '/app/assets/science-v240.js?v=4.37.0' in index
    assert 'const SCIENCE_CONTROLLER_SRC="/app/assets/science-v240.js?v=4.37.0"' in app
    assert 'async function ensureScienceController()' in app
    assert 'data-scsi-repair-loader' not in app  # DOM dataset property is used instead of unsafe markup injection.
    assert 'script.dataset.scsiRepairLoader="science-r4"' in app
    assert 'new URL(SCIENCE_CONTROLLER_SRC,window.SC_SITE_INTELLIGENCE_API||location.origin).href' in app
    assert 'const controller=await ensureScienceController()' in app
    assert 'Science controller did not expose its workspace surface.' in app


def test_science_controller_initializes_when_loaded_after_domcontentloaded():
    js=text("backend/public_app/assets/science-v240.js")
    assert 'REPAIR="4.37.0"' in js
    assert 'let bound=false;' in js
    assert 'if(bound)return;bound=true' in js
    assert 'if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",bind,{once:true});else bind()' in js
    assert 'return true}' in js


def test_ocean_waits_for_route_ownership_before_hydration():
    js=text("backend/public_app/assets/ocean-observation-v4360.js")
    assert 'await Promise.resolve(window.SCSIRouterV3228?.navigate?.("earth"))' in js
    assert 'panel.dataset.oceanWorkspaceOwner="earth:ocean"' in js
    assert 'document.body.dataset.workspaceMode="ocean"' in js
    assert 'window.SCSIProductionTruthV3231?.evaluate?.()' in js
    assert 'status:()=>({version:VERSION,repair:REPAIR' in js


def test_production_truth_certifies_ocean_mode_against_ocean_surface():
    js=text("backend/public_app/assets/production-truth-v3231.js")
    assert "function oceanModeActive()" in js
    assert "route==='earth'&&oceanModeActive()" in js
    assert "qs('#oceanObservationStudio')" in js
    assert "dataset.oceanHydrationState" in js
    assert "cards!==11" in js
    assert "Ocean Intelligence is ready · 11 marine systems visible." in js
    assert "'data-ocean-hydration-state'" in js
    assert "'scsi:ocean-observation-ready'" in js
    assert "'scsi:route-transition-start'" in js and "beginRoute(route)" in js
    assert "'scsi:route-transition-end'" in js


def test_r4_cache_namespace_and_assets_are_mirrored_to_wordpress():
    index=text("backend/public_app/index.html")
    sw=text("backend/public_app/service-worker.js")
    assert '/app/assets/production-truth-v3231.js?v=4.37.0' in index
    assert '/app/assets/bootstrap-v32361.js?v=4.37.0' in index
    assert 'const REPAIR="v4370"' in sw
    for name in ('app.js','science-v240.js','ocean-observation-v4360.js','production-truth-v3231.js','bootstrap-v32361.js'):
        assert (ROOT/'backend/public_app/assets'/name).read_bytes()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/name).read_bytes()
    assert (ROOT/'backend/public_app/index.html').read_bytes()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/index.html').read_bytes()


def test_science_discovery_reports_r4_release_lineage():
    source=text("backend/app/scientific_earth_systems_observatory.py")
    assert '"release_lineage": "v4.37.0"' in source


def test_ocean_and_space_are_first_class_featured_science_workspaces():
    index=text("backend/public_app/index.html")
    unified=text("backend/public_app/assets/unified-platform-v4000.css")
    app=text("backend/public_app/assets/app.js")
    science=text("backend/public_app/assets/science-v240.js")
    assert 'data-ocean-entry="hub" data-nav-group="analysis" data-nav-after-route="earth" data-nav-featured="true"' in index
    assert 'data-space-entry="hub" data-nav-group="places-systems" data-nav-after-route="science" data-nav-featured="true" data-route-alias="science"' in index
    assert '<span>Space</span><small>Orbital, planetary, astronomy &amp; SETI</small>' in index
    assert 'data-ocean-entry="hub">Explore Ocean</button>' in index
    assert 'data-space-entry="hub">Explore Space</button>' in index
    assert '<span>SPACE</span><h3>Space Intelligence</h3>' in index
    assert 'Featured science systems' in unified
    assert '/app/assets/unified-platform-v4000.css?v=4.37.0' in index
    assert 'async function openFeaturedScienceDomain(domain="space")' in app
    assert 'openFeaturedScienceDomain("space")' in app
    assert 'function openDomain(domain)' in science
    assert 'open,close,openDomain,openLocalWorkspace' in science
    assert (ROOT/'backend/public_app/index.html').read_bytes()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets/index.html').read_bytes()
    for name in ('app.js','science-v240.js','unified-platform-v4000.css'):
        assert (ROOT/'backend/public_app/assets'/name).read_bytes()==(ROOT/'wordpress-plugin/sustainable-catalyst-site-intelligence/assets'/name).read_bytes()
