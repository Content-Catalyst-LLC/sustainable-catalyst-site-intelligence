#!/usr/bin/env bash
set -Eeuo pipefail
PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v380-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then OWN_RUNTIME=1; fi
cleanup(){ if [[ "$OWN_RUNTIME" == "1" ]]; then rm -rf "$RUNTIME_DIR"; fi; }
trap cleanup EXIT
mkdir -p "$RUNTIME_DIR"
export SC_SI_LIVE_INTELLIGENCE_ROTATION_STATE_PATH="$RUNTIME_DIR/live-intelligence-rotation-state-v371.json"
export SC_SI_LIVE_INTELLIGENCE_ANALYTICS_STATE_PATH="$RUNTIME_DIR/live-intelligence-analytics-state-v372.json"
"$REPO_ROOT/scripts/run_v372_regression.sh" "$PYTHON_BIN" "$RUNTIME_DIR"
