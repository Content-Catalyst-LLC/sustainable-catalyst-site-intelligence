from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from fastapi import APIRouter, HTTPException

CONSUMER_VERSION = '4.40.0'
TARGET_KEY = 'site-intelligence'
PRODUCT = 'Site Intelligence'
CONSUMER_CONTRACT = 'sc-energy-runtime-site-intelligence-handoff/1.0'
HANDOFF_SCHEMA = "sc-energy-runtime-handoff/1.0"
RECEIPT_SCHEMA = "sc-energy-runtime-consumer-receipt/1.0"
EXPECTED_SECTIONS = ['identity', 'technologies_and_resources', 'global_context', 'provenance', 'review']
BOUNDARY = 'Handoff acceptance does not establish site suitability, current-year status, technical potential, or causal attribution.'

router = APIRouter(prefix="/v1/energy-runtime", tags=["energy-runtime-consumer"])


def _populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    if isinstance(value, dict):
        return any(_populated(v) for v in value.values())
    return True


def _unwrap(body: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Energy runtime handoff must be a JSON object")
    if body.get("schema") == HANDOFF_SCHEMA and isinstance(body.get("packet"), dict):
        return body["packet"], str(body.get("version") or "")
    if isinstance(body.get("handoff_id"), str) and isinstance(body.get("payload"), dict):
        return body, str((body.get("source") or {}).get("version") or "")
    raise HTTPException(status_code=422, detail="Expected sc-energy-runtime-handoff/1.0 wrapper or packet body")


def _validate(packet: dict[str, Any]) -> tuple[list[str], list[str], list[str], list[dict[str, str]]]:
    errors: list[str] = []
    target = packet.get("target") if isinstance(packet.get("target"), dict) else {}
    payload = packet.get("payload") if isinstance(packet.get("payload"), dict) else {}
    if not str(packet.get("handoff_id") or "").strip():
        errors.append("handoff_id is required")
    if target.get("key") != TARGET_KEY:
        errors.append(f"target.key must be {TARGET_KEY}")
    if target.get("consumer_contract") != CONSUMER_CONTRACT:
        errors.append(f"target.consumer_contract must be {CONSUMER_CONTRACT}")
    missing_sections = [s for s in EXPECTED_SECTIONS if s not in payload]
    if missing_sections:
        errors.append("payload is missing required target section(s): " + ", ".join(missing_sections))
    unexpected_sections = sorted(set(payload) - set(EXPECTED_SECTIONS))
    if unexpected_sections:
        errors.append("payload contains section(s) outside the target contract: " + ", ".join(unexpected_sections))
    populated = [s for s in EXPECTED_SECTIONS if s in payload and _populated(payload[s])]
    empty = [s for s in EXPECTED_SECTIONS if s not in populated]
    warnings: list[dict[str, str]] = []
    identity = payload.get("identity") if isinstance(payload.get("identity"), dict) else {}
    if not str(identity.get("study_id") or "").strip():
        warnings.append({"key":"missing-study-id","message":"identity.study_id is empty"})
    if not str(identity.get("question") or "").strip():
        warnings.append({"key":"missing-question","message":"identity.question is empty"})
    if not _populated(payload.get("provenance")):
        warnings.append({"key":"missing-provenance","message":"No provenance records are present"})
    return errors, populated, empty, warnings


def framework() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-energy-runtime-consumer-framework/1.0",
        "consumer_version": CONSUMER_VERSION,
        "target_key": TARGET_KEY,
        "product": PRODUCT,
        "accepted_handoff_schema": HANDOFF_SCHEMA,
        "consumer_contract": CONSUMER_CONTRACT,
        "expected_payload_sections": EXPECTED_SECTIONS,
        "mode": "ephemeral-validate-and-receipt",
        "capabilities": {
            "handoff_intake": True,
            "target_contract_validation": True,
            "payload_section_validation": True,
            "deterministic_receipt": True,
            "provenance_preservation": True,
            "automatic_execution": False,
            "persistence": False,
            "credential_forwarding": False,
            "automatic_ranking": False,
            "automatic_recommendation": False,
        },
        "boundary": BOUNDARY,
    }


def consume(body: dict[str, Any]) -> dict[str, Any]:
    packet, source_version = _unwrap(body)
    errors, populated, empty, warnings = _validate(packet)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors, "target": TARGET_KEY})
    canonical = json.dumps({"handoff_id":packet.get("handoff_id"),"target":packet.get("target"),"payload":packet.get("payload"),"contract_refs":packet.get("contract_refs",[])}, sort_keys=True, separators=(",", ":"))
    fingerprint = sha256(canonical.encode()).hexdigest()
    return {
        "ok": True,
        "schema": RECEIPT_SCHEMA,
        "consumer": {"product": PRODUCT, "target_key": TARGET_KEY, "app_version": CONSUMER_VERSION, "contract": CONSUMER_CONTRACT},
        "handoff_id": packet.get("handoff_id"),
        "source": {"product": (packet.get("source") or {}).get("product"), "subsystem": (packet.get("source") or {}).get("subsystem"), "energy_systems_version": source_version or (packet.get("source") or {}).get("version")},
        "accepted": True,
        "readiness": {"status": "accepted-with-warnings" if warnings else "accepted", "populated_sections": populated, "empty_sections": empty, "warnings": warnings},
        "contract_refs": list(packet.get("contract_refs") or []),
        "provenance": packet.get("payload", {}).get("provenance", []),
        "execution": {"performed": False, "mode": "not-executed"},
        "persistence": {"performed": False, "mode": "ephemeral"},
        "receipt_fingerprint": fingerprint,
        "boundary": BOUNDARY,
    }


@router.get("/consumer")
def energy_runtime_consumer_framework() -> dict[str, Any]:
    return framework()


@router.post("/consume")
def energy_runtime_consume(body: dict[str, Any]) -> dict[str, Any]:
    return consume(body)
