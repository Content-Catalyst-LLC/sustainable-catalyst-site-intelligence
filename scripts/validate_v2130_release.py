#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    "backend/app/version.py": [
        'APP_VERSION = "2.13.0"',
        'RELEASE_NAME = "Connector Operations and Data Ingestion Control Center"',
    ],
    "backend/app/config.py": [
        "connector_operations_enabled",
        "connector_operations_registry_path",
        "connector_operations_circuit_breaker_failures",
        "connector_operations_max_payload_bytes",
    ],
    "backend/app/connector_operations_v2130.py": [
        'SCHEMA_VERSION = "sc-site-intelligence-connector-operations/1.0"',
        "def run_due_jobs(",
        "def run_job(",
        "def resolve_quarantine(",
        '"raw_payload_persisted": False',
        "scheduler_boundary",
    ],
    "backend/app/main.py": [
        '"/public/connectors/operations"',
        '"/admin/connectors/control-center"',
        '"/admin/connectors/jobs/run-due"',
        '"/admin/connectors/quarantine/{quarantine_id}/resolve"',
    ],
    "backend/data/connector_operations_registry_v2130.json": [
        '"version": "2.13.0"',
        '"connector_id": "nasa_power"',
        '"connector_id": "sustainable_development"',
        '"triggers": [',
    ],
    "backend/tests/test_connector_operations_ingestion_control_v2130.py": [
        "test_v2130_registry_unifies_operational_connectors_without_secret_values",
        "test_run_due_jobs_executes_explicit_dry_run_batch",
        "test_quota_limit_blocks_live_run_but_force_can_override",
    ],
    "scripts/run_connector_jobs_v2130.py": [
        "--live",
        "--force",
        "run_due_jobs",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": [
        "Version: 2.13.0",
        "sc_public_connector_operations",
        "sc_connector_operations_control_center",
        "admin/connectors/control-center",
    ],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": [
        "connector-operations",
        "/public-connector-operations",
        "operational_status",
    ],
    "docs/V2130_CONNECTOR_OPERATIONS_DATA_INGESTION_CONTROL_CENTER.md": [
        "14 connector families",
        "Explicit scheduler boundary",
        "raw payloads are never persisted",
    ],
    "docs/RELEASE_MANIFEST_V2130.json": [
        '"connector_count": 14',
        '"job_count": 14',
        '"raw_payload_persistence": false',
        '"persistent_scheduler_claimed": false',
    ],
    "README.md": [
        "Current release:** v2.13.0",
        "/public/connectors/operations",
        "run_connector_jobs_v2130.py",
    ],
    "CHANGELOG.md": [
        "## 2.13.0 — Connector Operations and Data Ingestion Control Center",
    ],
}

for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")

registry = json.loads((ROOT / "backend/data/connector_operations_registry_v2130.json").read_text(encoding="utf-8"))
connectors = registry.get("connectors", [])
jobs = registry.get("jobs", [])
if registry.get("schema") != "sc-site-intelligence-connector-operations/1.0":
    raise SystemExit("Connector operations registry schema is invalid.")
if len(connectors) != 14 or len(jobs) != 14:
    raise SystemExit("Connector operations registry must contain 14 connectors and 14 jobs.")
connector_ids = {item.get("connector_id") for item in connectors}
if len(connector_ids) != 14 or None in connector_ids:
    raise SystemExit("Connector IDs must be unique.")
if any(job.get("connector_id") not in connector_ids for job in jobs):
    raise SystemExit("Every connector job must reference a registered connector.")
if any(set(job.get("triggers", [])) != {"manual", "scheduled", "conditional"} for job in jobs):
    raise SystemExit("Each v2.13.0 job must declare manual, scheduled, and conditional triggers.")

release = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2130.json").read_text(encoding="utf-8"))
if release.get("raw_payload_persistence") is not False:
    raise SystemExit("Release governance must prohibit raw payload persistence.")
if release.get("paid_scheduler_required") is not False or release.get("paid_database_required") is not False:
    raise SystemExit("Zero-cost release boundaries are missing.")

runtime_files = [
    "backend/data/connector_operations_state_v2130.json",
    "backend/data/connector_operations_history_v2130.jsonl",
    "backend/data/connector_operations_quarantine_v2130.jsonl",
    "backend/data/country_last_known_good.json",
]
for relative in runtime_files:
    if (ROOT / relative).exists():
        raise SystemExit(f"Runtime artifact must not be present in the immutable release: {relative}")

print("Site Intelligence v2.13.0 release contract passed.")
