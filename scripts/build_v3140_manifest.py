#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules', 'venv', '.venv'}
EXCLUDED_PREFIXES = {
    'backend/data/historical_archive_v2140', 'backend/data/spatial_evidence_v2150',
    'backend/data/statistical_harmonization_v2160', 'backend/data/model_governance_v2170',
    'backend/data/evidence_synthesis_v2180', 'backend/data/knowledge_graph_v2190',
    'backend/data/intelligence_publishing_v2200', 'backend/data/scheduled_monitoring_v2210',
    'backend/data/institutional_workspaces_v2220', 'backend/data/cross_platform_workflows_v2230',
    'backend/data/federation_exchange_v2240', 'backend/data/production_governance_v2250',
    'backend/data/live_intelligence_subscriptions_v390', 'backend/data/live_intelligence_briefings_v3100',
    'backend/data/live_intelligence_editorial_v3110', 'backend/data/live_intelligence_publication_v3120',
    'backend/data/live_intelligence_release_operations_v3130', 'backend/data/live_intelligence_change_history_v3140',
}
EXCLUDED_FILES = {
    'MANIFEST.json', '.DS_Store', 'backend/data/platform_core_queue.jsonl',
    'backend/data/country_last_known_good.json', 'backend/data/country_last_known_good.json.tmp',
    'backend/data/connector_operations_state_v2130.json', 'backend/data/connector_operations_state_v2130.json.tmp',
    'backend/data/connector_operations_history_v2130.jsonl', 'backend/data/connector_operations_quarantine_v2130.jsonl',
    'backend/data/live_intelligence_source_operations_state_v320.json',
    'backend/data/live_intelligence_source_operations_state_v320.json.tmp',
    'backend/data/live_intelligence_source_operations_history_v320.jsonl',
    'backend/data/live_intelligence_last_known_good_v361.json',
    'backend/data/live_intelligence_last_known_good_v361.json.tmp',
    'backend/data/live_intelligence_rotation_state_v371.json',
    'backend/data/live_intelligence_rotation_state_v371.json.tmp',
    'backend/data/live_intelligence_analytics_state_v372.json',
    'backend/data/live_intelligence_analytics_state_v372.json.tmp',
}

def included(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
        return False
    if rel in EXCLUDED_FILES or path.suffix in {'.pyc', '.pyo'}:
        return False
    return not any(rel == prefix or rel.startswith(prefix + '/') for prefix in EXCLUDED_PREFIXES)

files = []
for path in sorted((p for p in ROOT.rglob('*') if p.is_file() and included(p)), key=lambda p: p.relative_to(ROOT).as_posix()):
    data = path.read_bytes()
    files.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {
    'schema': 'sc-site-intelligence-release-manifest/1.0',
    'release': '3.22.0',
    'release_name': 'Corrections, Retractions, and Public Change History',
    'file_count': len(files),
    'files': files,
}
(ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(f"Wrote {len(files)}-file immutable release manifest.")
