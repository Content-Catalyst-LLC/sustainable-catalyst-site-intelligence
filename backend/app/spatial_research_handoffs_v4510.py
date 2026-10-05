from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .version import APP_VERSION

RESEARCH_OBJECT_SCHEMA = "sc-site-intelligence-spatial-research-object/1.0"
MANIFEST_SCHEMA = "sc-site-intelligence-spatial-research-manifest/1.0"
HANDOFF_SCHEMA = "sc-site-intelligence-cross-product-handoff/1.0"
PACKAGE_SCHEMA = "sc-site-intelligence-spatial-research-package/1.0"
REGISTRY_SCHEMA = "sc-site-intelligence-spatial-research-handoff-registry/1.0"
CONTRACT_VERSION = "1.0.0"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "spatial_research_handoff_registry_v4510.json"

_COMPONENT_FIELDS = (
    ("evidence_objects", "spatial-evidence"),
    ("query_results", "spatiotemporal-query-result"),
    ("graphs", "spatial-relationship-graph"),
    ("live_events", "live-geospatial-event"),
    ("federation_context", "source-federation-context"),
)
_SENSITIVE = re.compile(r"(?:api[_-]?key|password|secret|authorization|cookie|session[_-]?token|access[_-]?token|private[_-]?key)", re.I)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("Spatial research handoff registry schema mismatch")
    if payload.get("version") != APP_VERSION:
        raise ValueError("Spatial research handoff registry version does not match application version")
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


def _text(value: Any, limit: int = 1200) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _list(value: Any, limit: int = 100) -> list[Any]:
    return deepcopy(value[:limit]) if isinstance(value, list) else []


def _component_digest(record: Mapping[str, Any]) -> str:
    for key in ("content_digest", "result_digest", "graph_digest", "event_digest", "plan_digest", "digest", "fingerprint"):
        value = record.get(key)
        if isinstance(value, str) and value.startswith("sha256:"):
            return value
    integrity = record.get("integrity")
    if isinstance(integrity, Mapping):
        value = integrity.get("digest")
        if isinstance(value, str):
            return value if value.startswith("sha256:") else f"sha256:{value}"
    return _digest(record)


def _component_id(record: Mapping[str, Any], fallback: str) -> str:
    for key in ("object_id", "event_id", "graph_id", "result_id", "plan_id", "research_object_id", "source_id", "id"):
        value = _text(record.get(key), 240)
        if value:
            return value
    return fallback


def _normalize_scope(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, Mapping) else {}
    bbox = source.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in bbox):
        bbox = [float(v) for v in bbox]
    else:
        bbox = None
    return {
        "crs": _text(source.get("crs") or "EPSG:4326", 40),
        "bbox": bbox,
        "countries": [_text(x, 20).upper() for x in _list(source.get("countries"), 50) if _text(x, 20)],
        "regions": [_text(x, 120) for x in _list(source.get("regions"), 50) if _text(x, 120)],
        "date_start": _text(source.get("date_start") or source.get("start"), 80) or None,
        "date_end": _text(source.get("date_end") or source.get("end"), 80) or None,
    }


def registry_manifest() -> dict[str, Any]:
    registry = _registry()
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": CONTRACT_VERSION,
        "schema": registry["schema"],
        "research_object_schema": RESEARCH_OBJECT_SCHEMA,
        "manifest_schema": MANIFEST_SCHEMA,
        "handoff_schema": HANDOFF_SCHEMA,
        "package_schema": PACKAGE_SCHEMA,
        "target_count": len(registry["targets"]),
        "targets": deepcopy(registry["targets"]),
        "boundaries": deepcopy(registry["boundaries"]),
        "endpoints": {
            "object_schema": "/public/spatial-research/object-schema",
            "compose": "/public/spatial-research/objects/compose",
            "validate": "/public/spatial-research/objects/validate",
            "manifest": "/public/spatial-research/objects/manifest",
            "handoffs": "/public/spatial-research/handoffs",
            "handoff": "/public/spatial-research/handoff/{target}",
            "handoff_validate": "/public/spatial-research/handoff/{target}/validate",
            "package": "/public/spatial-research/package",
            "compatibility": "/public/spatial-research/compatibility",
        },
    }


def object_schema_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "schema": RESEARCH_OBJECT_SCHEMA,
        "required": ["title"],
        "components": [name for name, _ in _COMPONENT_FIELDS],
        "scope": {"crs": "EPSG:4326", "bbox": "optional [west,south,east,north]", "countries": "ISO-like codes", "date_start": "optional", "date_end": "optional"},
        "integrity": {"algorithm": "sha256", "content_addressed": True, "source_component_digests_preserved": True},
        "persistence": {"server_persistence": False, "automatic_remote_write": False},
    }


def compose_research_object(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("Spatial research request must be an object")
    issues = _scan_sensitive(request)
    if issues:
        raise ValueError("; ".join(issues[:5]))
    title = _text(request.get("title"), 300)
    if not title:
        raise ValueError("title is required")

    components: dict[str, list[dict[str, Any]]] = {}
    lineage: list[dict[str, Any]] = []
    for field, component_type in _COMPONENT_FIELDS:
        raw = request.get(field)
        if field == "federation_context" and isinstance(raw, Mapping):
            raw = [raw]
        rows = [deepcopy(row) for row in _list(raw, 500 if field in {"evidence_objects", "live_events"} else 100) if isinstance(row, Mapping)]
        components[field] = rows
        for index, row in enumerate(rows):
            digest = _component_digest(row)
            lineage.append({
                "component_type": component_type,
                "component_id": _component_id(row, f"{component_type}-{index+1}"),
                "schema": _text(row.get("schema"), 240) or None,
                "digest": digest,
            })

    core = {
        "schema": RESEARCH_OBJECT_SCHEMA,
        "version": APP_VERSION,
        "title": title,
        "research_question": _text(request.get("research_question") or request.get("question"), 3000),
        "scope": _normalize_scope(request.get("scope")),
        "tags": [_text(x, 100) for x in _list(request.get("tags"), 50) if _text(x, 100)],
        "components": components,
        "findings": _list(request.get("findings"), 100),
        "assumptions": _list(request.get("assumptions"), 100),
        "uncertainties": _list(request.get("uncertainties"), 100),
        "evidence_gaps": _list(request.get("evidence_gaps"), 100),
        "notes": _list(request.get("notes"), 100),
        "visual_state": deepcopy(request.get("visual_state")) if isinstance(request.get("visual_state"), Mapping) else {},
        "lineage": sorted(lineage, key=lambda row: (row["component_type"], row["component_id"], row["digest"])),
    }
    digest = _digest(core)
    research_object = {
        **core,
        "research_object_id": _text(request.get("research_object_id"), 240) or f"spatial-research:{digest.split(':', 1)[1][:24]}",
        "research_digest": digest,
        "source_component_digests": sorted({row["digest"] for row in lineage}),
        "boundaries": deepcopy(_registry()["boundaries"]),
        "persistence": {"server_persistence": False, "automatic_remote_write": False, "delivery_attempted": False},
    }
    return {"ok": True, "version": APP_VERSION, "research_object": research_object}


def validate_research_object(request: Mapping[str, Any]) -> dict[str, Any]:
    obj = request.get("research_object") if isinstance(request, Mapping) and isinstance(request.get("research_object"), Mapping) else request
    if not isinstance(obj, Mapping):
        raise ValueError("research_object must be an object")
    errors: list[str] = []
    warnings: list[str] = []
    if obj.get("schema") != RESEARCH_OBJECT_SCHEMA:
        errors.append("schema-mismatch")
    if obj.get("version") != APP_VERSION:
        errors.append("version-mismatch")
    if not _text(obj.get("research_object_id"), 240):
        errors.append("research-object-id-missing")
    if not _text(obj.get("title"), 300):
        errors.append("title-missing")
    components = obj.get("components")
    if not isinstance(components, Mapping):
        errors.append("components-missing")
    if not isinstance(obj.get("lineage"), list):
        errors.append("lineage-missing")
    if not obj.get("source_component_digests"):
        warnings.append("no-source-component-digests")
    supplied_digest = obj.get("research_digest")
    core = {k: deepcopy(v) for k, v in obj.items() if k not in {"research_object_id", "research_digest", "source_component_digests", "boundaries", "persistence"}}
    expected_digest = _digest(core)
    if supplied_digest != expected_digest:
        errors.append("research-digest-mismatch")
    return {
        "ok": not errors,
        "version": APP_VERSION,
        "schema": RESEARCH_OBJECT_SCHEMA,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "expected_research_digest": expected_digest,
    }


def research_manifest(request: Mapping[str, Any]) -> dict[str, Any]:
    obj = request.get("research_object") if isinstance(request, Mapping) and isinstance(request.get("research_object"), Mapping) else compose_research_object(request)["research_object"]
    validation = validate_research_object(obj)
    if not validation["valid"]:
        raise ValueError("Invalid spatial research object: " + ", ".join(validation["errors"]))
    counts = {field: len(obj["components"].get(field) or []) for field, _ in _COMPONENT_FIELDS}
    source_ids: set[str] = set()
    for rows in obj["components"].values():
        for row in rows:
            source = row.get("source") if isinstance(row, Mapping) else None
            if isinstance(source, Mapping):
                sid = _text(source.get("source_id") or source.get("feed_id"), 240)
                if sid:
                    source_ids.add(sid)
            sid = _text(row.get("source_id"), 240) if isinstance(row, Mapping) else ""
            if sid:
                source_ids.add(sid)
    payload = {
        "schema": MANIFEST_SCHEMA,
        "version": APP_VERSION,
        "research_object_id": obj["research_object_id"],
        "research_digest": obj["research_digest"],
        "title": obj["title"],
        "research_question": obj.get("research_question"),
        "scope": deepcopy(obj.get("scope") or {}),
        "component_counts": counts,
        "source_ids": sorted(source_ids),
        "source_component_digests": list(obj.get("source_component_digests") or []),
        "evidence_gap_count": len(obj.get("evidence_gaps") or []),
    }
    payload["manifest_digest"] = _digest(payload)
    return {"ok": True, **payload}


def handoff_registry() -> dict[str, Any]:
    registry = _registry()
    return {"ok": True, "version": APP_VERSION, "schema": registry["schema"], "targets": deepcopy(registry["targets"]), "boundaries": deepcopy(registry["boundaries"])}


def _target(target: str) -> dict[str, Any]:
    target = _text(target, 80).lower()
    match = next((row for row in _registry()["targets"] if row["target_id"] == target), None)
    if not match:
        raise ValueError("Unsupported handoff target")
    return deepcopy(match)


def _ensure_research_object(request: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(request.get("research_object"), Mapping):
        obj = deepcopy(request["research_object"])
        validation = validate_research_object(obj)
        if not validation["valid"]:
            raise ValueError("Invalid spatial research object: " + ", ".join(validation["errors"]))
        return obj
    if isinstance(request.get("research"), Mapping):
        return compose_research_object(request["research"])["research_object"]
    return compose_research_object(request)["research_object"]


def create_handoff(target: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("Handoff request must be an object")
    target_spec = _target(target)
    obj = _ensure_research_object(request)
    manifest = research_manifest({"research_object": obj})
    components = obj["components"]
    common = {
        "research_object_id": obj["research_object_id"],
        "research_digest": obj["research_digest"],
        "title": obj["title"],
        "research_question": obj.get("research_question"),
        "scope": deepcopy(obj.get("scope") or {}),
        "source_component_digests": list(obj.get("source_component_digests") or []),
    }
    if target_spec["target_id"] == "workspace":
        payload = {**common, "project_type": "spatial-research", "portable_state": {"components": deepcopy(components), "visual_state": deepcopy(obj.get("visual_state") or {})}, "resume_supported": True}
    elif target_spec["target_id"] == "knowledge-library":
        payload = {**common, "manifest": {k: deepcopy(v) for k, v in manifest.items() if k != "ok"}, "evidence_objects": deepcopy(components.get("evidence_objects") or []), "federation_context": deepcopy(components.get("federation_context") or []), "automatic_publication": False}
    elif target_spec["target_id"] == "research-librarian":
        payload = {**common, "source_ids": manifest["source_ids"], "evidence_gaps": deepcopy(obj.get("evidence_gaps") or []), "findings": deepcopy(obj.get("findings") or []), "guidance_only": True}
    elif target_spec["target_id"] == "research-lab":
        payload = {**common, "study_inputs": {"evidence_objects": deepcopy(components.get("evidence_objects") or []), "query_results": deepcopy(components.get("query_results") or []), "graphs": deepcopy(components.get("graphs") or [])}, "hypotheses": _list(request.get("hypotheses"), 100), "reproducible": True}
    elif target_spec["target_id"] == "workbench":
        payload = {**common, "computational_inputs": {"evidence_objects": deepcopy(components.get("evidence_objects") or []), "query_results": deepcopy(components.get("query_results") or [])}, "assumptions": deepcopy(obj.get("assumptions") or []), "derived_results_must_preserve_lineage": True}
    elif target_spec["target_id"] == "decision-studio":
        payload = {**common, "findings": deepcopy(obj.get("findings") or []), "assumptions": deepcopy(obj.get("assumptions") or []), "uncertainties": deepcopy(obj.get("uncertainties") or []), "scenarios": _list(request.get("scenarios"), 100), "exposure_context": deepcopy(components.get("live_events") or []), "decision_not_automated": True}
    else:  # platform-core
        payload = {**common, "object_schema": RESEARCH_OBJECT_SCHEMA, "manifest_schema": MANIFEST_SCHEMA, "lineage": deepcopy(obj.get("lineage") or []), "contract_refs": ["v4.46-spatial-evidence", "v4.47-spatiotemporal", "v4.48-spatial-graph", "v4.49-live-geospatial", "v4.50-source-federation"]}

    packet_core = {
        "schema": HANDOFF_SCHEMA,
        "version": APP_VERSION,
        "target": target_spec["target_id"],
        "target_label": target_spec["label"],
        "packet_type": target_spec["packet_type"],
        "payload": payload,
        "preview_only": True,
        "delivery_attempted": False,
        "delivery_verified": False,
        "human_confirmation_required": True,
        "source_research_digest": obj["research_digest"],
    }
    packet = {**packet_core, "handoff_id": f"spatial-handoff:{_digest(packet_core).split(':', 1)[1][:24]}"}
    packet["handoff_digest"] = _digest(packet_core)
    return {"ok": True, "version": APP_VERSION, "packet": packet, "boundaries": deepcopy(_registry()["boundaries"])}


def validate_handoff(target: str, request: Mapping[str, Any]) -> dict[str, Any]:
    target_spec = _target(target)
    packet = request.get("packet") if isinstance(request, Mapping) and isinstance(request.get("packet"), Mapping) else request
    if not isinstance(packet, Mapping):
        raise ValueError("packet must be an object")
    errors: list[str] = []
    if packet.get("schema") != HANDOFF_SCHEMA:
        errors.append("schema-mismatch")
    if packet.get("version") != APP_VERSION:
        errors.append("version-mismatch")
    if packet.get("target") != target_spec["target_id"]:
        errors.append("target-mismatch")
    if packet.get("delivery_attempted") is not False:
        errors.append("delivery-boundary-violated")
    core = {k: deepcopy(v) for k, v in packet.items() if k not in {"handoff_id", "handoff_digest"}}
    expected = _digest(core)
    if packet.get("handoff_digest") != expected:
        errors.append("handoff-digest-mismatch")
    return {"ok": not errors, "version": APP_VERSION, "valid": not errors, "target": target_spec["target_id"], "errors": errors, "expected_handoff_digest": expected}


def build_package(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("Package request must be an object")
    obj = _ensure_research_object(request)
    manifest = research_manifest({"research_object": obj})
    requested_targets = request.get("targets")
    if requested_targets is None:
        requested_targets = [row["target_id"] for row in _registry()["targets"]]
    if not isinstance(requested_targets, list):
        raise ValueError("targets must be an array")
    packets = [create_handoff(str(target), {"research_object": obj, "scenarios": request.get("scenarios"), "hypotheses": request.get("hypotheses")})["packet"] for target in requested_targets]
    package_core = {
        "schema": PACKAGE_SCHEMA,
        "version": APP_VERSION,
        "research_object": obj,
        "manifest": {k: deepcopy(v) for k, v in manifest.items() if k != "ok"},
        "handoffs": packets,
        "target_count": len(packets),
        "export_only": True,
        "server_persistence": False,
        "delivery_attempted": False,
    }
    package_digest = _digest(package_core)
    package = {**package_core, "package_id": f"spatial-research-package:{package_digest.split(':', 1)[1][:24]}", "package_digest": package_digest}
    return {"ok": True, "version": APP_VERSION, "package": package}


def compatibility_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": APP_VERSION,
        "v4_46_spatial_evidence": {"status": "preserved-and-consumed", "mutation": False},
        "v4_47_spatiotemporal": {"status": "preserved-and-consumed", "mutation": False},
        "v4_48_spatial_graph": {"status": "preserved-and-consumed", "mutation": False},
        "v4_49_live_geospatial": {"status": "preserved-and-consumed", "impact_semantics": "potential-exposure-not-confirmed-impact"},
        "v4_50_source_federation": {"status": "preserved-and-consumed", "trust_separate_from_authority": True},
        "legacy_research_handoffs": {"status": "preserved", "replacement": "v4.51 spatial-research handoff packets"},
        "wordpress_role": "thin-shell-and-embed-bridge",
        "delivery_attempted": False,
        "server_persistence": False,
    }
