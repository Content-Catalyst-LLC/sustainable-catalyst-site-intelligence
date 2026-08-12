"""Public-safe, runtime-generated deployment receipt for Site Intelligence v4.35.14."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import os
from typing import Any

from .build_info import public_build_info
from .version import APP_VERSION

DEFAULT_RELEASE_ID = f"site-intelligence-v{APP_VERSION}"
_RECEIPT_STARTED_AT = datetime.now(timezone.utc).isoformat()


def _value(name: str, fallback: str = "unavailable") -> str:
    return (os.getenv(name) or fallback).strip()


def public_deployment_receipt() -> dict[str, Any]:
    build = public_build_info()
    deployment = dict(build["deployment"])
    release_id = _value("SC_SI_RELEASE_ID", DEFAULT_RELEASE_ID)
    commit = str(deployment.get("git_commit", "unavailable"))
    branch = str(deployment.get("git_branch", "unavailable"))
    service_id = str(deployment.get("service_id", "unavailable"))
    material = "|".join([release_id, APP_VERSION, commit, branch, service_id])
    receipt_fingerprint = sha256(material.encode("utf-8")).hexdigest()[:24]
    platform = str(deployment.get("platform", "local"))
    identity_complete = platform != "render" or all(value != "unavailable" for value in (commit, branch, service_id))
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_id": release_id,
        "receipt_fingerprint": receipt_fingerprint,
        "receipt_state": "verified-runtime" if identity_complete else "incomplete-runtime",
        "identity_complete": identity_complete,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "process_started_at": _RECEIPT_STARTED_AT,
        "deployment": deployment,
        "cache_policy": "no-store",
    }
