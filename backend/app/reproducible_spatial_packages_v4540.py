from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .spatial_research_handoffs_v4510 import validate_research_object
from .version import APP_VERSION

PACKAGE_SCHEMA = "sc-site-intelligence-reproducible-spatial-intelligence-package/1.0"
MANIFEST_SCHEMA = "sc-site-intelligence-reproducible-spatial-package-manifest/1.0"
VERIFICATION_SCHEMA = "sc-site-intelligence-reproducible-spatial-package-verification/1.0"
REPRODUCTION_PLAN_SCHEMA = "sc-site-intelligence-spatial-reproduction-plan/1.0"
EXPORT_PLAN_SCHEMA = "sc-site-intelligence-spatial-package-export-plan/1.0"
COMPARISON_SCHEMA = "sc-site-intelligence-spatial-package-comparison/1.0"
RESEARCH_CONTEXT_SCHEMA = "sc-site-intelligence-spatial-package-research-context/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-reproducible-spatial-package-registry/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "reproducible_spatial_package_registry_v4540.json"

_SENSITIVE = re.compile(r"(?:api[_-]?key|password|secret|authorization|cookie|session[_-]?token|access[_-]?token|private[_-]?key)", re.I)
_DIGEST_KEYS = (
    "package_digest", "research_digest", "content_digest", "result_digest", "graph_digest",
    "event_digest", "plan_digest", "prediction_digest", "scenario_digest", "change_digest",
    "exposure_digest", "threshold_digest", "analysis_digest", "digest", "fingerprint",
)
_COMPONENT_GROUPS = (
    "evidence_objects", "query_results", "graphs", "live_events", "federation_context",
    "predictions", "scenarios", "changes", "exposures", "thresholds", "advanced_domain_context",
)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, limit: int = 1600) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA or payload.get("version") != APP_VERSION:
        raise ValueError("Reproducible spatial package registry does not match runtime")
    return payload


def _scan_sensitive(value: Any, path: str = "payload") -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _SENSITIVE.search(str(key)):
                issues.append(f"Sensitive field is not allowed: {child_path}")
            issues.extend(_scan_sensitive(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_sensitive(child, f"{path}[{index}]") )
    return issues


def _entry_digest(value: Mapping[str, Any]) -> str:
    for key in _DIGEST_KEYS:
        found = value.get(key)
        if isinstance(found, str) and found.startswith("sha256:"):
            return found
    integrity = value.get("integrity")
    if isinstance(integrity, Mapping):
        found = integrity.get("digest")
        if isinstance(found, str) and found:
            return found if found.startswith("sha256:") else f"sha256:{found}"
    return _digest(value)


def _entry_id(value: Mapping[str, Any], fallback: str) -> str:
    for key in (
        "research_object_id", "object_id", "result_id", "graph_id", "event_id", "plan_id",
        "prediction_id", "scenario_id", "change_id", "exposure_id", "threshold_id", "domain_id", "id",
    ):
        found = _text(value.get(key), 240)
        if found:
            return found
    return fallback


def registry_manifest() -> dict[str, Any]:
    r = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        **deepcopy(r),
        "profile_count": len(r["profiles"]),
        "export_target_count": len(r["export_targets"]),
    }


def schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schemas": {
            "package": PACKAGE_SCHEMA,
            "manifest": MANIFEST_SCHEMA,
            "verification": VERIFICATION_SCHEMA,
            "reproduction_plan": REPRODUCTION_PLAN_SCHEMA,
            "export_plan": EXPORT_PLAN_SCHEMA,
            "comparison": COMPARISON_SCHEMA,
            "research_context": RESEARCH_CONTEXT_SCHEMA,
        },
        "component_groups": list(_COMPONENT_GROUPS),
        "boundaries": deepcopy(_registry()["boundaries"]),
    }


def profiles_manifest() -> dict[str, Any]:
    r = _registry()
    return {"ok": True, "version": APP_VERSION, "profiles": deepcopy(r["profiles"]), "default_profile": r["default_profile"]}


def _normalize_research_object(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("research_object must be an object")
    validation = validate_research_object({"research_object": value})
    if validation.get("valid") is not True:
        raise ValueError("research_object failed integrity validation")
    return deepcopy(dict(value))


def _normalize_components(request: Mapping[str, Any], profile: str) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    components: dict[str, list[dict[str, Any]]] = {}
    inventory: list[dict[str, Any]] = []
    for group in _COMPONENT_GROUPS:
        raw = request.get(group, [])
        if group in {"federation_context", "advanced_domain_context"} and isinstance(raw, Mapping):
            raw = [raw]
        rows = [deepcopy(x) for x in raw if isinstance(x, Mapping)] if isinstance(raw, list) else []
        components[group] = rows
        for index, row in enumerate(rows):
            digest = _entry_digest(row)
            inventory.append({
                "group": group,
                "entry_id": _entry_id(row, f"{group}-{index+1}"),
                "schema": _text(row.get("schema"), 240) or None,
                "digest": digest,
                "inclusion_mode": "embedded-snapshot" if profile == "portable-snapshot" else "reference-with-optional-snapshot",
            })
    inventory.sort(key=lambda x: (x["group"], x["entry_id"], x["digest"]))
    return components, inventory


def compose_package(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("package request must be an object")
    issues = _scan_sensitive(request)
    if issues:
        raise ValueError("; ".join(issues[:5]))
    title = _text(request.get("title"), 300)
    if not title:
        raise ValueError("title is required")
    registry = _registry()
    profile = _text(request.get("profile"), 80) or registry["default_profile"]
    allowed = {x["profile_id"] for x in registry["profiles"]}
    if profile not in allowed:
        raise ValueError(f"unsupported profile: {profile}")
    research_object = _normalize_research_object(request.get("research_object"))
    components, inventory = _normalize_components(request, profile)
    if research_object is not None:
        inventory.append({
            "group": "research_object",
            "entry_id": research_object["research_object_id"],
            "schema": research_object.get("schema"),
            "digest": research_object["research_digest"],
            "inclusion_mode": "embedded-snapshot" if profile == "portable-snapshot" else "reference-with-optional-snapshot",
        })
        inventory.sort(key=lambda x: (x["group"], x["entry_id"], x["digest"]))

    manifest_core = {
        "schema": MANIFEST_SCHEMA,
        "version": APP_VERSION,
        "profile": profile,
        "entry_count": len(inventory),
        "entries": inventory,
        "source_digests": sorted({x["digest"] for x in inventory}),
        "reproducibility": {
            "content_addressed": True,
            "deterministic_manifest": True,
            "automatic_execution": False,
            "automatic_remote_fetch": False,
            "automatic_remote_write": False,
        },
    }
    manifest_digest = _digest(manifest_core)
    manifest = {**manifest_core, "manifest_digest": manifest_digest}
    package_core = {
        "schema": PACKAGE_SCHEMA,
        "version": APP_VERSION,
        "title": title,
        "description": _text(request.get("description"), 3000) or None,
        "profile": profile,
        "research_object": research_object,
        "components": components,
        "manifest": manifest,
        "assumptions": deepcopy(request.get("assumptions") or []),
        "uncertainties": deepcopy(request.get("uncertainties") or []),
        "evidence_gaps": deepcopy(request.get("evidence_gaps") or []),
        "notes": deepcopy(request.get("notes") or []),
        "boundaries": deepcopy(registry["boundaries"]),
    }
    package_digest = _digest(package_core)
    package = {
        **package_core,
        "package_id": _text(request.get("package_id"), 240) or f"spatial-package:{package_digest.split(':',1)[1][:24]}",
        "package_digest": package_digest,
        "sealed": True,
        "delivery_attempted": False,
        "execution_attempted": False,
    }
    return {"ok": True, "version": APP_VERSION, "package": package}


def verify_package(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        raise ValueError("package is required")
    issues = _scan_sensitive(package)
    errors = list(issues)
    if package.get("schema") != PACKAGE_SCHEMA:
        errors.append("package schema mismatch")
    if package.get("version") != APP_VERSION:
        errors.append("package version mismatch")
    manifest = package.get("manifest") if isinstance(package.get("manifest"), Mapping) else {}
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest schema mismatch")
    manifest_core = {k: deepcopy(v) for k,v in manifest.items() if k != "manifest_digest"}
    expected_manifest_digest = _digest(manifest_core)
    if manifest.get("manifest_digest") != expected_manifest_digest:
        errors.append("manifest digest mismatch")
    package_core = {k: deepcopy(v) for k,v in package.items() if k not in {"package_id","package_digest","sealed","delivery_attempted","execution_attempted"}}
    expected_package_digest = _digest(package_core)
    if package.get("package_digest") != expected_package_digest:
        errors.append("package digest mismatch")
    research_object = package.get("research_object")
    if isinstance(research_object, Mapping):
        validation = validate_research_object({"research_object": research_object})
        if validation.get("valid") is not True:
            errors.append("research object integrity mismatch")
    result = {
        "schema": VERIFICATION_SCHEMA,
        "version": APP_VERSION,
        "valid": not errors,
        "errors": errors,
        "package_id": package.get("package_id"),
        "observed_package_digest": package.get("package_digest"),
        "expected_package_digest": expected_package_digest,
        "manifest_digest": manifest.get("manifest_digest"),
        "entry_count": manifest.get("entry_count", 0),
        "automatic_execution": False,
        "automatic_repair": False,
    }
    result["verification_digest"] = _digest(result)
    return {"ok": not errors, "version": APP_VERSION, "verification": result}


def inspect_package(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        raise ValueError("package is required")
    verification = verify_package({"package": package})["verification"]
    manifest = package.get("manifest") if isinstance(package.get("manifest"), Mapping) else {}
    by_group: dict[str,int] = {}
    for entry in manifest.get("entries", []):
        if isinstance(entry, Mapping):
            group = str(entry.get("group") or "unknown")
            by_group[group] = by_group.get(group, 0) + 1
    return {
        "ok": True,
        "version": APP_VERSION,
        "inspection": {
            "package_id": package.get("package_id"),
            "package_digest": package.get("package_digest"),
            "title": package.get("title"),
            "profile": package.get("profile"),
            "valid": verification["valid"],
            "entry_count": manifest.get("entry_count", 0),
            "groups": by_group,
            "sealed": package.get("sealed") is True,
            "execution_attempted": package.get("execution_attempted") is True,
            "delivery_attempted": package.get("delivery_attempted") is True,
        },
    }


def build_manifest(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        package = compose_package(request)["package"]
    manifest = deepcopy(package.get("manifest") or {})
    return {"ok": True, "version": APP_VERSION, "manifest": manifest}


def reproduction_plan(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        raise ValueError("package is required")
    verification = verify_package({"package": package})["verification"]
    manifest = package.get("manifest") if isinstance(package.get("manifest"), Mapping) else {}
    steps = [
        "verify-package-and-manifest-digests",
        "resolve-source-components-by-content-digest",
        "restore-spatial-research-object-and-scope",
        "restore-query-graph-live-source-and-domain-context",
        "restore-predictive-scenario-change-exposure-threshold-context",
        "validate-runtime-and-schema-compatibility",
        "require-human-authorization-before-any-compute-rerun",
        "record-new-execution-receipts-without-overwriting-original-artifacts",
    ]
    core = {
        "schema": REPRODUCTION_PLAN_SCHEMA,
        "version": APP_VERSION,
        "package_id": package.get("package_id"),
        "package_digest": package.get("package_digest"),
        "package_valid": verification["valid"],
        "required_source_digests": deepcopy(manifest.get("source_digests") or []),
        "steps": steps,
        "automatic_execution": False,
        "automatic_network_fetch": False,
        "human_authorization_required": True,
        "original_artifacts_mutated": False,
    }
    core["plan_digest"] = _digest(core)
    return {"ok": True, "version": APP_VERSION, "reproduction_plan": core}


def export_plan(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        raise ValueError("package is required")
    target = _text(request.get("target"), 120)
    targets = {x["target_id"]: x for x in _registry()["export_targets"]}
    if target not in targets:
        raise ValueError(f"unsupported export target: {target}")
    verification = verify_package({"package": package})["verification"]
    core = {
        "schema": EXPORT_PLAN_SCHEMA,
        "version": APP_VERSION,
        "target": target,
        "target_contract": deepcopy(targets[target]),
        "package_id": package.get("package_id"),
        "package_digest": package.get("package_digest"),
        "package_valid": verification["valid"],
        "preview_only": True,
        "delivery_attempted": False,
        "remote_write_attempted": False,
        "human_confirmation_required": True,
    }
    core["export_plan_digest"] = _digest(core)
    return {"ok": True, "version": APP_VERSION, "export_plan": core}


def compare_packages(request: Mapping[str, Any]) -> dict[str, Any]:
    packages = [x for x in request.get("packages", []) if isinstance(x, Mapping)] if isinstance(request, Mapping) else []
    if len(packages) < 2:
        raise ValueError("at least two packages are required")
    rows=[]
    for package in packages:
        verification=verify_package({"package":package})["verification"]
        rows.append({
            "package_id":package.get("package_id"),
            "package_digest":package.get("package_digest"),
            "profile":package.get("profile"),
            "entry_count":(package.get("manifest") or {}).get("entry_count",0),
            "valid":verification["valid"],
        })
    core={
        "schema":COMPARISON_SCHEMA,
        "version":APP_VERSION,
        "package_count":len(rows),
        "packages":rows,
        "automatic_package_ranking":False,
        "preferred_package":None,
        "human_review_required":True,
    }
    core["comparison_digest"]=_digest(core)
    return {"ok":True,"version":APP_VERSION,"comparison":core}


def research_context(request: Mapping[str, Any]) -> dict[str, Any]:
    package = request.get("package") if isinstance(request, Mapping) else None
    if not isinstance(package, Mapping):
        raise ValueError("package is required")
    research_object = package.get("research_object")
    if not isinstance(research_object, Mapping):
        raise ValueError("package does not contain a research_object")
    validation=validate_research_object({"research_object":research_object})
    if validation.get("valid") is not True:
        raise ValueError("research_object failed integrity validation")
    core={
        "schema":RESEARCH_CONTEXT_SCHEMA,
        "version":APP_VERSION,
        "package_id":package.get("package_id"),
        "package_digest":package.get("package_digest"),
        "research_object_id":research_object.get("research_object_id"),
        "research_digest":research_object.get("research_digest"),
        "source_component_digests":deepcopy(research_object.get("source_component_digests") or []),
        "research_object_mutated":False,
        "package_mutated":False,
    }
    core["context_digest"]=_digest(core)
    return {"ok":True,"version":APP_VERSION,"research_context":core}


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "preserves": [
            "v4.46-spatial-evidence", "v4.47-spatiotemporal-analysis", "v4.48-spatial-relationship-graph",
            "v4.49-live-geospatial-fusion", "v4.50-global-source-federation", "v4.51-spatial-research-objects",
            "v4.52-predictive-spatial-intelligence", "v4.53-scenario-exposure-change", "v4.53-advanced-domain-workspaces",
        ],
        "boundaries": deepcopy(_registry()["boundaries"]),
        "execution_authority": "external-compute-runtime-or-human-authorized-reproduction-only",
        "site_intelligence_automatic_execution": False,
    }
