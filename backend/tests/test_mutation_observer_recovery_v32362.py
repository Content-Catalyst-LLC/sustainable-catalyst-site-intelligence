from __future__ import annotations
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[2]
CLIENT=TestClient(app)
def read(path:str)->str:return (ROOT/path).read_text(encoding="utf-8")
def test_public_mutation_observer_recovery_contract():
    response=CLIENT.get("/public/mutation-observer-recovery")
    assert response.status_code==200
    payload=response.json()
    assert payload["ok"] is True
    assert payload["version"]=="4.35.17"
    assert payload["mutation_observer"]["self_observation_prevented"] is True
    assert payload["complete_shell_gate"]["required"] is True
    assert payload["complete_shell_gate"]["skip_allowed"] is False
def test_browser_reliability_observer_is_idempotent_debounced_and_bounded():
    js=read("backend/public_app/assets/browser-reliability-v3235.js")
    for token in ("summary.textContent!==nextText","requestAnimationFrame(flushMapSummaries)","state.observer?.disconnect()","MAX_SUMMARY_PASSES_PER_SECOND=8","closest?.('.scsi-map-summary')"):
        assert token in js
    assert "new MutationObserver(()=>updateMapSummaries())" not in js
    assert read("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/browser-reliability-v3235.js")==js
def test_runtime_health_and_version_include_recovery_contract():
    health=CLIENT.get("/public/runtime-health").json()
    assert health["ok"] is True
    assert health["version"]=="4.35.17"
    assert "/public/mutation-observer-recovery" in {row["path"] for row in health["endpoint_contracts"]}
    check={row["id"]:row for row in health["checks"]}["mutation-observer-recovery"]
    assert check["status"]=="pass"
def test_complete_shell_browser_gate_is_mandatory_in_release_verifier():
    verify=read("verify_site_intelligence_v3_23_6_2_macos.sh")
    assert "browser_complete_shell_gate_v32362.py" in verify
    assert "SC_SI_SKIP_BROWSER_SMOKE" not in verify
    gate=read("scripts/browser_complete_shell_gate_v32362.py")
    assert "ERROR: Chromium or Chrome is required" in gate
    assert "ERROR: Playwright is required" in gate
    assert "SCSIDataTruthV32371" in gate and "SCSIProductionTruthV3231" in gate
def test_wordpress_release_is_current_and_host_isolated():
    php=read("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
    assert "Version: 4.35.17" in php
    assert "wp_enqueue_script('scsi-browser-reliability'" not in php
