#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "backend/app/version.py": ['APP_VERSION = "3.8.0"'],
    "backend/app/config.py": ["live_intelligence_rotation_enabled", "live_intelligence_rotation_state_path", "live_intelligence_rotation_window_hours"],
    "backend/app/live_intelligence_rotation_v371.py": [
        "ROTATION_SCHEMA_VERSION", "class LiveIntelligenceRotationStore", "def score_rotation_candidate(",
        "def select_rotation_signals(", "def apply_rotation_policy(", "def rotation_policy(",
        "individual_user_tracking", "automatic_emergency_publication",
    ],
    "backend/app/main.py": [
        "/public/live-intelligence/rotation-policy", "/public/live-intelligence/rotation-status",
        "/admin/live-intelligence/rotation", "apply_live_intelligence_rotation_policy",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 3.8.0", "rest_live_intelligence_rotation_policy", "rest_live_intelligence_rotation_status",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "data-rotation-rank", "data-rotation-score", "data-rotation-override", "rotation_reasons",
    ],
    "README.md": ["v3.8.0 — Signal Relevance and Rotation Intelligence"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V371.md": ["Signal Relevance and Rotation Intelligence", "aggregate signal-display history"],
    "docs/RELEASE_MANIFEST_V371.json": [
        '"version": "3.8.0"', '"individual_user_tracking": false',
        '"automatic_emergency_publication": false', '"override_changes_observation": false',
    ],
}
for relative, needles in REQUIRED.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
print("Site Intelligence v3.8.0 release contract passed.")
