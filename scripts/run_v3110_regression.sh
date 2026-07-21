#!/usr/bin/env bash
set -Eeuo pipefail
PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3110-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then OWN_RUNTIME=1; fi
cleanup(){ if [[ "$OWN_RUNTIME" == "1" ]]; then rm -rf "$RUNTIME_DIR"; fi; }
trap cleanup EXIT
mkdir -p "$RUNTIME_DIR/editorial"
export SC_SI_LIVE_INTELLIGENCE_EDITORIAL_WORKSPACES_PATH="$RUNTIME_DIR/editorial/workspaces.jsonl"
export SC_SI_LIVE_INTELLIGENCE_EDITORIAL_EVENTS_PATH="$RUNTIME_DIR/editorial/events.jsonl"
export SC_SI_LIVE_INTELLIGENCE_EDITORIAL_ORCHESTRATION_PATH="$RUNTIME_DIR/editorial/orchestration.jsonl"
"$REPO_ROOT/scripts/run_v3100_regression.sh" "$PYTHON_BIN" "$RUNTIME_DIR"
"$PYTHON_BIN" "$REPO_ROOT/scripts/validate_v3110_release.py"
