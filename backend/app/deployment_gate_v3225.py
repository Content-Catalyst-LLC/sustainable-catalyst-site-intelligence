"""Release-installation gate and deployment identity for v3.23.1."""

from __future__ import annotations

from hashlib import sha256
import os
from typing import Any

from .build_info import public_build_info
from .version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _value(name: str, fallback: str = "unavailable") -> str:
    return (os.getenv(name) or fallback).strip()


def _commit_matches(observed: str, expected: str) -> bool:
    if not expected:
        return True
    if not observed or observed == "unavailable":
        return False
    return observed == expected or observed.startswith(expected) or expected.startswith(observed)


def build_release_gate(plugin_version: str | None = None, expected_commit: str | None = None) -> dict[str, Any]:
    build = public_build_info()
    deployment = dict(build["deployment"])
    platform = str(deployment.get("platform", "local"))
    branch = str(deployment.get("git_branch", "unavailable"))
    commit = str(deployment.get("git_commit", "unavailable"))
    repository = str(deployment.get("git_repository", "unavailable"))

    expected_branch = _value("SC_SI_EXPECTED_GIT_BRANCH", "main")
    release_channel = _value("SC_SI_RELEASE_CHANNEL", "production")
    rollback_tag = _value("SC_SI_ROLLBACK_TAG")
    normalized_plugin = (plugin_version or "").strip()
    normalized_commit = (expected_commit or "").strip()

    plugin_compatible = not normalized_plugin or normalized_plugin == EXPECTED_WORDPRESS_PLUGIN_VERSION
    branch_verified = platform != "render" or branch == expected_branch
    identity_available = platform != "render" or (commit != "unavailable" and branch != "unavailable")
    commit_verified = _commit_matches(commit, normalized_commit)
    production_channel = release_channel == "production"

    checks = {
        "backend_version_current": build["backend_version"] == APP_VERSION,
        "plugin_compatible": plugin_compatible,
        "deployment_identity_available": identity_available,
        "branch_verified": branch_verified,
        "commit_verified": commit_verified,
        "production_channel": production_channel,
    }
    install_allowed = all(checks.values())

    reasons: list[str] = []
    if not checks["plugin_compatible"]:
        reasons.append(
            f"WordPress plugin v{normalized_plugin or 'unknown'} does not match backend v{EXPECTED_WORDPRESS_PLUGIN_VERSION}."
        )
    if not checks["deployment_identity_available"]:
        reasons.append("Render did not expose a verifiable Git branch and commit.")
    if not checks["branch_verified"]:
        reasons.append(f"Render is on branch {branch}; expected {expected_branch}.")
    if not checks["commit_verified"]:
        reasons.append(f"Render commit {commit} does not match requested commit {normalized_commit}.")
    if not checks["production_channel"]:
        reasons.append(f"Release channel is {release_channel}; expected production.")

    fingerprint_material = "|".join([APP_VERSION, repository, branch, commit, release_channel])
    release_fingerprint = sha256(fingerprint_material.encode("utf-8")).hexdigest()[:20]

    if install_allowed:
        state = "ready" if platform == "render" else "local-validation"
    else:
        state = "blocked"

    return {
        "ok": True,
        "version": APP_VERSION,
        "backend_version": APP_VERSION,
        "expected_wordpress_plugin_version": EXPECTED_WORDPRESS_PLUGIN_VERSION,
        "release_name": RELEASE_NAME,
        "release_channel": release_channel,
        "release_fingerprint": release_fingerprint,
        "gate_state": state,
        "install_allowed": install_allowed,
        "checks": checks,
        "reasons": reasons,
        "requested": {
            "plugin_version": normalized_plugin or None,
            "expected_commit": normalized_commit or None,
        },
        "deployment": deployment,
        "rollback": {
            "ready": rollback_tag != "unavailable",
            "tag": rollback_tag,
        },
        "cache_policy": "no-store",
    }
