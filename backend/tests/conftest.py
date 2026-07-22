"""Regression hygiene for writable runtime state.

The release repository intentionally excludes file-backed runtime archives,
connector receipts, and source-health state. Tests may exercise default paths,
so clean those generated artifacts after each test to keep order-independent
release-contract checks deterministic.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
_RUNTIME_DIRS = [
    "historical_archive_v2140",
    "production_governance_v2250",
    "federation_exchange_v2240",
    "cross_platform_workflows_v2230",
    "institutional_workspaces_v2220",
    "scheduled_monitoring_v2210",
    "intelligence_publishing_v2200",
    "knowledge_graph_v2190",
    "evidence_synthesis_v2180",
    "model_governance_v2170",
    "statistical_harmonization_v2160",
    "spatial_evidence_v2150",
    "live_intelligence_registry_governance_v3190",
]
_RUNTIME_FILES = [
    "country_last_known_good.json",
    "country_last_known_good.json.tmp",
    "platform_core_queue.jsonl",
    "connector_operations_state_v2130.json",
    "connector_operations_state_v2130.json.tmp",
    "connector_operations_history_v2130.jsonl",
    "connector_operations_quarantine_v2130.jsonl",
    "live_intelligence_source_operations_state_v320.json",
    "live_intelligence_source_operations_state_v320.json.tmp",
    "live_intelligence_source_operations_history_v320.jsonl",
    "live_intelligence_last_known_good_v361.json",
    "live_intelligence_last_known_good_v361.json.tmp",
    "live_intelligence_rotation_state_v371.json",
    "live_intelligence_rotation_state_v371.json.tmp",
]


def _clean_runtime_state() -> None:
    for name in _RUNTIME_DIRS:
        shutil.rmtree(DATA / name, ignore_errors=True)
    for name in _RUNTIME_FILES:
        try:
            (DATA / name).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture(autouse=True)
def release_runtime_hygiene():
    _clean_runtime_state()
    yield
    _clean_runtime_state()
