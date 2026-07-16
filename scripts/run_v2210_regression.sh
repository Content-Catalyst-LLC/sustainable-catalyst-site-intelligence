#!/usr/bin/env bash
set -Eeuo pipefail

PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v2210-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then
  OWN_RUNTIME=1
fi
cleanup() {
  if [[ "$OWN_RUNTIME" == "1" ]]; then
    rm -rf "$RUNTIME_DIR"
  fi
}
trap cleanup EXIT

mkdir -p "$RUNTIME_DIR"/{country,history,spatial,harmonization,models,evidence,graph,publishing,monitoring,connectors,platform}
export PYTHONDONTWRITEBYTECODE=1
export SC_SI_EXTERNAL_LIVE=false
export SC_SI_PUBLIC_CONNECTOR_LIVE_CHECKS=false
export SC_SI_COUNTRY_CACHE_PATH="$RUNTIME_DIR/country/country_last_known_good.json"
export SC_SI_HISTORICAL_ARCHIVE_ROOT_PATH="$RUNTIME_DIR/history"
export SC_SI_HISTORICAL_ARCHIVE_INDEX_PATH="$RUNTIME_DIR/history/snapshot_index_v2140.jsonl"
export SC_SI_HISTORICAL_ARCHIVE_CHANGE_PATH="$RUNTIME_DIR/history/change_events_v2140.jsonl"
export SC_SI_HISTORICAL_ARCHIVE_REVISION_PATH="$RUNTIME_DIR/history/revision_events_v2140.jsonl"
export SC_SI_HISTORICAL_ARCHIVE_RETENTION_LOG_PATH="$RUNTIME_DIR/history/retention_events_v2140.jsonl"
export SC_SI_SPATIAL_EVIDENCE_ROOT_PATH="$RUNTIME_DIR/spatial"
export SC_SI_SPATIAL_EVIDENCE_AREAS_PATH="$RUNTIME_DIR/spatial/areas_v2150.jsonl"
export SC_SI_SPATIAL_EVIDENCE_DATASETS_PATH="$RUNTIME_DIR/spatial/datasets_v2150.jsonl"
export SC_SI_SPATIAL_EVIDENCE_ANALYSIS_PATH="$RUNTIME_DIR/spatial/analyses_v2150.jsonl"
export SC_SI_STATISTICAL_HARMONIZATION_ROOT_PATH="$RUNTIME_DIR/harmonization"
export SC_SI_STATISTICAL_HARMONIZATION_SERIES_INDEX_PATH="$RUNTIME_DIR/harmonization/series_index_v2160.jsonl"
export SC_SI_STATISTICAL_HARMONIZATION_LINEAGE_PATH="$RUNTIME_DIR/harmonization/transformation_lineage_v2160.jsonl"
export SC_SI_MODEL_GOVERNANCE_ROOT_PATH="$RUNTIME_DIR/models"
export SC_SI_MODEL_GOVERNANCE_MODELS_PATH="$RUNTIME_DIR/models/models_v2170.jsonl"
export SC_SI_MODEL_GOVERNANCE_FORECASTS_PATH="$RUNTIME_DIR/models/forecasts_v2170.jsonl"
export SC_SI_MODEL_GOVERNANCE_EVALUATIONS_PATH="$RUNTIME_DIR/models/evaluations_v2170.jsonl"
export SC_SI_MODEL_GOVERNANCE_WARNING_RULES_PATH="$RUNTIME_DIR/models/warning_rules_v2170.jsonl"
export SC_SI_MODEL_GOVERNANCE_WARNING_EVENTS_PATH="$RUNTIME_DIR/models/warning_events_v2170.jsonl"
export SC_SI_EVIDENCE_SYNTHESIS_ROOT_PATH="$RUNTIME_DIR/evidence"
export SC_SI_EVIDENCE_SYNTHESIS_CLAIMS_PATH="$RUNTIME_DIR/evidence/claims_v2180.jsonl"
export SC_SI_EVIDENCE_SYNTHESIS_EVIDENCE_PATH="$RUNTIME_DIR/evidence/evidence_v2180.jsonl"
export SC_SI_EVIDENCE_SYNTHESIS_REVIEWS_PATH="$RUNTIME_DIR/evidence/reviews_v2180.jsonl"
export SC_SI_EVIDENCE_SYNTHESIS_SYNTHESES_PATH="$RUNTIME_DIR/evidence/syntheses_v2180.jsonl"
export SC_SI_EVIDENCE_SYNTHESIS_UNCERTAINTY_PATH="$RUNTIME_DIR/evidence/uncertainty_v2180.jsonl"
export SC_SI_KNOWLEDGE_GRAPH_ROOT_PATH="$RUNTIME_DIR/graph"
export SC_SI_KNOWLEDGE_GRAPH_ENTITIES_PATH="$RUNTIME_DIR/graph/entities_v2190.jsonl"
export SC_SI_KNOWLEDGE_GRAPH_RELATIONSHIPS_PATH="$RUNTIME_DIR/graph/relationships_v2190.jsonl"
export SC_SI_KNOWLEDGE_GRAPH_ALIASES_PATH="$RUNTIME_DIR/graph/aliases_v2190.jsonl"
export SC_SI_INTELLIGENCE_PUBLISHING_ROOT_PATH="$RUNTIME_DIR/publishing"
export SC_SI_INTELLIGENCE_PUBLISHING_PROJECTS_PATH="$RUNTIME_DIR/publishing/projects_v2200.jsonl"
export SC_SI_INTELLIGENCE_PUBLISHING_BLOCKS_PATH="$RUNTIME_DIR/publishing/blocks_v2200.jsonl"
export SC_SI_INTELLIGENCE_PUBLISHING_REVIEWS_PATH="$RUNTIME_DIR/publishing/reviews_v2200.jsonl"
export SC_SI_INTELLIGENCE_PUBLISHING_VERSIONS_PATH="$RUNTIME_DIR/publishing/versions_v2200.jsonl"
export SC_SI_SCHEDULED_MONITORING_ROOT_PATH="$RUNTIME_DIR/monitoring"
export SC_SI_SCHEDULED_MONITORING_MONITORS_PATH="$RUNTIME_DIR/monitoring/monitors_v2210.jsonl"
export SC_SI_SCHEDULED_MONITORING_CHECKS_PATH="$RUNTIME_DIR/monitoring/checks_v2210.jsonl"
export SC_SI_SCHEDULED_MONITORING_ALERTS_PATH="$RUNTIME_DIR/monitoring/alerts_v2210.jsonl"
export SC_SI_SCHEDULED_MONITORING_DIGESTS_PATH="$RUNTIME_DIR/monitoring/digests_v2210.jsonl"
export SC_SI_SCHEDULED_MONITORING_DELIVERIES_PATH="$RUNTIME_DIR/monitoring/deliveries_v2210.jsonl"
export SC_SI_SCHEDULED_MONITORING_FEEDS_PATH="$RUNTIME_DIR/monitoring/feeds_v2210.jsonl"
export SC_SI_CONNECTOR_OPERATIONS_STATE_PATH="$RUNTIME_DIR/connectors/state.json"
export SC_SI_CONNECTOR_OPERATIONS_HISTORY_PATH="$RUNTIME_DIR/connectors/history.jsonl"
export SC_SI_CONNECTOR_OPERATIONS_QUARANTINE_PATH="$RUNTIME_DIR/connectors/quarantine.jsonl"
export SC_SI_PLATFORM_CORE_QUEUE_PATH="$RUNTIME_DIR/platform/queue.jsonl"

cd "$REPO_ROOT/backend"
"$PYTHON_BIN" -m pytest -q
