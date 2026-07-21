from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]

def test_release_contract_markers():
    checks={
      "backend/app/version.py":["3.13.0","Connected Public Intelligence and Evidence Platform"],
      "backend/app/cross_platform_workflows_v2230.py":["class CrossPlatformWorkflowCenter","def create_packet(","def record_receipt(","def retry_failed(","def add_linkback("],
      "backend/public_app/index.html":["data-route=\"workflows\"","id=\"crossPlatformWorkflowStudio\""],
      "backend/public_app/service-worker.js":["/app/assets/workflows-v2230.js","/app/assets/workflows-v2230.css"],
      "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 3.13.0","sc_public_cross_platform_workflows","sc_cross_platform_workflows_control_center"],
      "README.md":["Current release:** v3.13.0 — Connected Public Intelligence and Evidence Platform"],
    }
    for rel,markers in checks.items():
      text=(ROOT/rel).read_text()
      for marker in markers: assert marker in text,f"{rel}: {marker}"

def test_governance_manifest_blocks_unsafe_claims():
    data=json.loads((ROOT/"docs/RELEASE_MANIFEST_V2230.json").read_text())
    assert data["typed_routes"]==12 and data["platforms"]==7
    assert data["automatic_remote_write"] is False
    assert data["automatic_retry"] is False
    assert data["persistent_message_broker_included"] is False
    assert data["account_provisioning"] is False
    assert data["public_packet_payloads"] is False
    assert data["individual_tracking"] is False

def test_public_app_loader_and_wp_rest_proxy():
    app=(ROOT/"backend/public_app/assets/app.js").read_text()
    php=(ROOT/"wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text()
    assert "SCCrossPlatformWorkflowsV2230" in app
    assert "public-cross-platform-workflows" in php
