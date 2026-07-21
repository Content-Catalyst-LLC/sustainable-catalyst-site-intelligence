from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def test_v371_release_contract_markers():
    requirements = {
        "backend/app/version.py": ['APP_VERSION = "3.13.0"'],
        "backend/app/live_intelligence_rotation_v371.py": [
            "ROTATION_SCHEMA_VERSION", "LiveIntelligenceRotationStore", "score_rotation_candidate",
            "select_rotation_signals", "apply_rotation_policy", "rotation_policy",
        ],
        "backend/app/main.py": [
            "/public/live-intelligence/rotation-policy", "/public/live-intelligence/rotation-status",
            "/admin/live-intelligence/rotation", "limit=24",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
            "Version: 3.13.0", "rest_live_intelligence_rotation_policy", "rest_live_intelligence_rotation_status",
        ],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
            "data-rotation-rank", "data-rotation-score", "data-rotation-override", "rotation_reasons",
        ],
        "README.md": ["v3.13.0 — Signal Relevance and Rotation Intelligence"],
        "docs/RELEASE_MANIFEST_V371.json": [
            '"version": "3.13.0"', '"individual_user_tracking": false',
            '"automatic_emergency_publication": false', '"override_changes_observation": false',
        ],
    }
    for relative, needles in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {relative}"


def test_admin_rotation_override_endpoint_requires_human_approval(tmp_path):
    settings = Settings(live_intelligence_rotation_state_path=str(tmp_path / "rotation.json"))
    main.app.dependency_overrides[main.get_settings] = lambda: settings
    client = TestClient(main.app)
    try:
        rejected = client.patch("/admin/live-intelligence/rotation/signals/test.signal", json={
            "mode": "pin", "reason": "Needs context",
        })
        accepted = client.patch("/admin/live-intelligence/rotation/signals/test.signal", json={
            "mode": "pin", "reason": "Human-reviewed public-interest context", "human_approved": True,
        })
        state = client.get("/admin/live-intelligence/rotation")
    finally:
        main.app.dependency_overrides.pop(main.get_settings, None)
    assert rejected.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json()["override"]["changes_observation"] is False
    assert state.status_code == 200
    assert state.json()["status"]["active_override_count"] == 1
