"""Public cartographic interaction contract for Site Intelligence v4.17.0."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .version import APP_VERSION

POLICY_PATH = Path(__file__).resolve().parent.parent / "data" / "map_interaction_policy_v3232.json"


def public_map_interaction_contract() -> dict[str, Any]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    payload["ok"] = True
    payload["version"] = APP_VERSION
    payload["release_id"] = f"site-intelligence-v{APP_VERSION}"
    payload["layer_controls"] = {
        "base_style": True,
        "imagery_opacity": True,
        "event_visibility": True,
        "event_clustering": True,
        "category_filter": True,
        "source_filter": True,
        "recency_filter": True,
        "fit_results": True,
        "reset_view": True,
        "shareable_state": True,
    }
    payload["interaction_contract"] = {
        "list_to_map_selection": "synchronized",
        "map_to_list_selection": "synchronized",
        "keyboard_navigation": "supported",
        "cluster_expansion": "zoom-and-reveal",
        "empty_overlay_behavior": "retain-basemap",
        "inactive_workspace_loading": "disabled",
    }
    return payload
