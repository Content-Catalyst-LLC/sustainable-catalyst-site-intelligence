from __future__ import annotations

import json
from pathlib import Path

from .version import APP_VERSION

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "standalone_functional_parity_registry_v45532.json"

def _registry() -> dict:
    data = json.loads(REGISTRY_PATH.read_text())
    if data.get("version") != APP_VERSION:
        raise ValueError("Standalone functional parity registry version mismatch")
    return data

def manifest() -> dict:
    r=_registry()
    return {"ok": True, "version": APP_VERSION, "schema": r["schema"], "release_name": r["release_name"], "strategy": r["strategy"], "authority": r["authority"], "workspace_count": len(r["required_workspaces"]), "functional_control_count": len(r["functional_controls"])}

def routes() -> dict:
    r=_registry(); return {"ok":True,"version":APP_VERSION,"deep_link_aliases":r["deep_link_aliases"],"required_workspaces":r["required_workspaces"]}

def certification() -> dict:
    r=_registry(); return {"ok":True,"version":APP_VERSION,"certification":r["certification"],"api_transport":r["api_transport"],"functional_controls":r["functional_controls"]}
