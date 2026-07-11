"""Public-safe build metadata for release compatibility checks."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

from .version import APP_VERSION, API_SCHEMA_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME

_BUILD_STARTED_AT = datetime.now(timezone.utc).isoformat()


def public_build_info() -> dict[str, Any]:
    commit = (os.getenv("RENDER_GIT_COMMIT") or os.getenv("SC_SI_GIT_COMMIT") or "unavailable").strip()
    build_timestamp = (os.getenv("SC_SI_BUILD_TIMESTAMP") or _BUILD_STARTED_AT).strip()
    return {
        "ok": True,
        "version": APP_VERSION,
        "backend_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "expected_wordpress_plugin_version": EXPECTED_WORDPRESS_PLUGIN_VERSION,
        "release_name": RELEASE_NAME,
        "git_commit": commit,
        "build_timestamp": build_timestamp,
        "platform_core_optional": True,
    }
