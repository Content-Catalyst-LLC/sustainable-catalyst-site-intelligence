#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    '.git', '__pycache__', '.pytest_cache',
    'production_governance_v2250', 'federation_exchange_v2240',
    'cross_platform_workflows_v2230', 'institutional_workspaces_v2220',
    'scheduled_monitoring_v2210', 'intelligence_publishing_v2200',
    'knowledge_graph_v2190', 'evidence_synthesis_v2180',
    'model_governance_v2170', 'statistical_harmonization_v2160',
    'spatial_evidence_v2150', 'historical_archive_v2140',
}
EXCLUDED_FILES = {
    'MANIFEST.json', '.DS_Store', 'country_last_known_good.json',
    'country_last_known_good.json.tmp', 'platform_core_queue.jsonl',
    'connector_operations_state_v2130.json',
    'connector_operations_state_v2130.json.tmp',
    'connector_operations_history_v2130.jsonl',
    'connector_operations_quarantine_v2130.jsonl',
    'live_intelligence_source_operations_state_v320.json',
    'live_intelligence_source_operations_state_v320.json.tmp',
    'live_intelligence_source_operations_history_v320.jsonl',
}
records = []
for path in sorted(ROOT.rglob('*')):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        continue
    if path.name in EXCLUDED_FILES or path.suffix in {'.pyc', '.pyo'}:
        continue
    data = path.read_bytes()
    records.append({'path': rel.as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {
    'schema': 'sc-site-intelligence-release-manifest/1.0',
    'release': '3.5.0',
    'release_name': 'Topic and Regional Channels',
    'file_count': len(records),
    'files': records,
}
(ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(len(records))
