"""Writable runtime-state path isolation for Site Intelligence v4.35.18."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_runtime_path(configured: str, runtime_root: str | None = None) -> Path:
    """Resolve writable state outside the immutable checkout when a runtime root is set."""
    path = Path(str(configured)).expanduser()
    if path.is_absolute():
        return path
    root_value = (runtime_root or os.getenv("SC_SI_RUNTIME_STATE_ROOT") or "").strip()
    if not root_value:
        return path
    parts = list(path.parts)
    if parts[:2] == ["backend", "data"]:
        parts = parts[2:]
    elif parts[:1] == ["data"]:
        parts = parts[1:]
    relative = Path(*parts) if parts else Path(path.name)
    return Path(root_value).expanduser() / relative
