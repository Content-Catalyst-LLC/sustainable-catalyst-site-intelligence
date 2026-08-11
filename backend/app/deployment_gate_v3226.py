"""Resume-safe release gate and deployment identity for v4.35.4."""

from __future__ import annotations

from hashlib import sha256
import os
from typing import Any

from .build_info import public_build_info
from .deployment_receipt_v3226 import DEFAULT_RELEASE_ID, public_deployment_receipt
from .version import APP_VERSION, EXPECTED_WORDPRESS_PLUGIN_VERSION, RELEASE_NAME


def _value(name: str, fallback: str = "unavailable") -> str:
    return (os.getenv(name) or fallback).strip()


def _matches(observed: str, expected: str) -> bool:
    if not expected:
        return True
    if not observed or observed == "unavailable":
        return False
    return observed == expected or observed.startswith(expected) or expected.startswith(observed)


def build_release_gate(plugin_version: str | None = None, expected_commit: str | None = None, expected_release_id: str | None = None) -> dict[str, Any]:
    build = public_build_info()
    receipt = public_deployment_receipt()
    deployment = dict(build["deployment"])
    platform = str(deployment.get("platform", "local"))
    branch = str(deployment.get("git_branch", "unavailable"))
    commit = str(deployment.get("git_commit", "unavailable"))
    repository = str(deployment.get("git_repository", "unavailable"))
    release_id = str(receipt.get("release_id") or DEFAULT_RELEASE_ID)
    expected_branch = _value("SC_SI_EXPECTED_GIT_BRANCH", "main")
    release_channel = _value("SC_SI_RELEASE_CHANNEL", "production")
    rollback_tag = _value("SC_SI_ROLLBACK_TAG")
    normalized_plugin = (plugin_version or "").strip()
    normalized_commit = (expected_commit or "").strip()
    normalized_release_id = (expected_release_id or "").strip()
    checks = {
        "backend_version_current": build["backend_version"] == APP_VERSION,
        "plugin_compatible": not normalized_plugin or normalized_plugin == EXPECTED_WORDPRESS_PLUGIN_VERSION,
        "deployment_identity_available": platform != "render" or bool(receipt.get("identity_complete")),
        "branch_verified": platform != "render" or branch == expected_branch,
        "commit_verified": _matches(commit, normalized_commit),
        "release_id_verified": not normalized_release_id or release_id == normalized_release_id,
        "production_channel": release_channel == "production",
    }
    install_allowed = all(checks.values())
    reasons: list[str] = []
    if not checks["plugin_compatible"]:
        reasons.append(f"WordPress plugin v{normalized_plugin or 'unknown'} does not match backend v{EXPECTED_WORDPRESS_PLUGIN_VERSION}.")
    if not checks["deployment_identity_available"]:
        reasons.append("Render did not expose a complete deployment receipt.")
    if not checks["branch_verified"]:
        reasons.append(f"Render is on branch {branch}; expected {expected_branch}.")
    if not checks["commit_verified"]:
        reasons.append(f"Render commit {commit} does not match requested commit {normalized_commit}.")
    if not checks["release_id_verified"]:
        reasons.append(f"Runtime release id {release_id} does not match requested release id {normalized_release_id}.")
    if not checks["production_channel"]:
        reasons.append(f"Release channel is {release_channel}; expected production.")
    material = "|".join([APP_VERSION, release_id, repository, branch, commit, release_channel])
    state = ("ready" if platform == "render" else "local-validation") if install_allowed else "blocked"
    return {
        "ok": True,
        "version": APP_VERSION,
        "backend_version": APP_VERSION,
        "expected_wordpress_plugin_version": EXPECTED_WORDPRESS_PLUGIN_VERSION,
        "release_name": RELEASE_NAME,
        "release_id": release_id,
        "release_channel": release_channel,
        "release_fingerprint": sha256(material.encode("utf-8")).hexdigest()[:20],
        "deployment_receipt": receipt,
        "gate_state": state,
        "install_allowed": install_allowed,
        "checks": checks,
        "reasons": reasons,
        "requested": {"plugin_version": normalized_plugin or None, "expected_commit": normalized_commit or None, "expected_release_id": normalized_release_id or None},
        "deployment": deployment,
        "rollback": {"ready": rollback_tag != "unavailable", "tag": rollback_tag},
        "cache_policy": "no-store",
    }
