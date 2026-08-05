"""Public-safe build and deployment metadata for release compatibility checks."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import os
from typing import Any

from .version import APP_VERSION, API_SCHEMA_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME

_BUILD_STARTED_AT = datetime.now(timezone.utc).isoformat()


def _value(name: str, fallback: str = "unavailable") -> str:
    return (os.getenv(name) or fallback).strip()


def public_build_info() -> dict[str, Any]:
    commit = _value("RENDER_GIT_COMMIT", _value("SC_SI_GIT_COMMIT"))
    branch = _value("RENDER_GIT_BRANCH", _value("SC_SI_GIT_BRANCH"))
    repo_slug = _value("RENDER_GIT_REPO_SLUG", "Content-Catalyst-LLC/sustainable-catalyst-site-intelligence")
    service_id = _value("RENDER_SERVICE_ID")
    service_name = _value("RENDER_SERVICE_NAME", "sustainable-catalyst-site-intelligence")
    external_url = _value("RENDER_EXTERNAL_URL")
    instance_id = _value("RENDER_INSTANCE_ID")
    build_timestamp = _value("SC_SI_BUILD_TIMESTAMP", _BUILD_STARTED_AT)
    platform = "render" if service_id != "unavailable" or external_url != "unavailable" else "local"
    release_channel = _value("SC_SI_RELEASE_CHANNEL", "production")
    release_id = _value("SC_SI_RELEASE_ID", f"site-intelligence-v{APP_VERSION}")
    expected_branch = _value("SC_SI_EXPECTED_GIT_BRANCH", "main")
    fingerprint_material = "|".join([APP_VERSION, release_id, repo_slug, branch, commit, release_channel])
    release_fingerprint = sha256(fingerprint_material.encode("utf-8")).hexdigest()[:20]

    deployment = {
        "platform": platform,
        "service_id": service_id,
        "service_name": service_name,
        "external_url": external_url,
        "instance_id": instance_id,
        "git_repository": repo_slug,
        "git_branch": branch,
        "git_commit": commit,
        "git_commit_short": commit[:12] if commit != "unavailable" else "unavailable",
        "release_version": APP_VERSION,
        "release_id": release_id,
        "auto_deploy_contract": "commit",
        "health_check_path": "/health",
        "expected_git_branch": expected_branch,
        "release_channel": release_channel,
        "release_fingerprint": release_fingerprint,
    }

    return {
        "ok": True,
        "version": APP_VERSION,
        "backend_version": APP_VERSION,
        "api_schema_version": API_SCHEMA_VERSION,
        "expected_wordpress_plugin_version": EXPECTED_WORDPRESS_PLUGIN_VERSION,
        "release_name": RELEASE_NAME,
        "git_commit": commit,
        "git_branch": branch,
        "git_repository": repo_slug,
        "build_timestamp": build_timestamp,
        "release_channel": release_channel,
        "release_id": release_id,
        "release_fingerprint": release_fingerprint,
        "cache_policy": "no-store",
        "platform_core_optional": True,
        "deployment": deployment,
    }


def public_deployment_status() -> dict[str, Any]:
    build = public_build_info()
    return {
        "ok": True,
        "version": APP_VERSION,
        "backend_version": build["backend_version"],
        "expected_wordpress_plugin_version": build["expected_wordpress_plugin_version"],
        "release_id": build["release_id"],
        "deployment": build["deployment"],
        "verification_endpoints": {
            "health": "/health",
            "build_info": "/public/build-info",
            "deployment_status": "/public/deployment-status",
            "deployment_receipt": "/public/deployment-receipt",
            "release_gate": "/public/release-gate",
        },
    }
