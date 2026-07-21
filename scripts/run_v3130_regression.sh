#!/usr/bin/env bash
set -Eeuo pipefail
PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3130-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then OWN_RUNTIME=1; fi
cleanup(){ if [[ "$OWN_RUNTIME" == "1" ]]; then rm -rf "$RUNTIME_DIR"; fi; }
trap cleanup EXIT
mkdir -p "$RUNTIME_DIR/release-operations"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_DEPLOYMENTS_PATH="$RUNTIME_DIR/release-operations/deployments.jsonl"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_OPERATION_EVENTS_PATH="$RUNTIME_DIR/release-operations/events.jsonl"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_ISSUES_PATH="$RUNTIME_DIR/release-operations/issues.jsonl"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_CORRECTIONS_PATH="$RUNTIME_DIR/release-operations/corrections.jsonl"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_ROLLBACKS_PATH="$RUNTIME_DIR/release-operations/rollbacks.jsonl"
export SC_SI_LIVE_INTELLIGENCE_RELEASE_OPERATION_HANDOFFS_PATH="$RUNTIME_DIR/release-operations/handoffs.jsonl"
"$REPO_ROOT/scripts/run_v3120_regression.sh" "$PYTHON_BIN" "$RUNTIME_DIR"
"$PYTHON_BIN" "$REPO_ROOT/scripts/validate_v3130_release.py"
