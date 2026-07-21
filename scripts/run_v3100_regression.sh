#!/usr/bin/env bash
set -Eeuo pipefail
PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3100-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then OWN_RUNTIME=1; fi
cleanup(){ if [[ "$OWN_RUNTIME" == "1" ]]; then rm -rf "$RUNTIME_DIR"; fi; }
trap cleanup EXIT
mkdir -p "$RUNTIME_DIR/subscriptions" "$RUNTIME_DIR/briefings"
export SC_SI_LIVE_INTELLIGENCE_BRIEFINGS_PATH="$RUNTIME_DIR/briefings/briefings.jsonl"
export SC_SI_LIVE_INTELLIGENCE_BRIEFING_PACKAGES_PATH="$RUNTIME_DIR/briefings/packages.jsonl"
export SC_SI_LIVE_INTELLIGENCE_BRIEFING_HANDOFFS_PATH="$RUNTIME_DIR/briefings/handoffs.jsonl"
"$REPO_ROOT/scripts/run_v390_regression.sh" "$PYTHON_BIN" "$RUNTIME_DIR"
"$PYTHON_BIN" "$REPO_ROOT/scripts/validate_v3100_release.py"
