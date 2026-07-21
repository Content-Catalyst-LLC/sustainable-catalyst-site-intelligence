#!/usr/bin/env bash
set -Eeuo pipefail
PYTHON_BIN="${1:-python3}"
RUNTIME_DIR="${2:-$(mktemp -d "${TMPDIR:-/tmp}/scsi-v3120-regression.XXXXXX")}" 
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWN_RUNTIME=0
if [[ $# -lt 2 ]]; then OWN_RUNTIME=1; fi
cleanup(){ if [[ "$OWN_RUNTIME" == "1" ]]; then rm -rf "$RUNTIME_DIR"; fi; }
trap cleanup EXIT
mkdir -p "$RUNTIME_DIR/publication"
export SC_SI_LIVE_INTELLIGENCE_PUBLICATION_RELEASES_PATH="$RUNTIME_DIR/publication/releases.jsonl"
export SC_SI_LIVE_INTELLIGENCE_PUBLICATION_RELEASE_EVENTS_PATH="$RUNTIME_DIR/publication/events.jsonl"
export SC_SI_LIVE_INTELLIGENCE_PUBLICATION_HANDOFFS_PATH="$RUNTIME_DIR/publication/handoffs.jsonl"
"$REPO_ROOT/scripts/run_v3110_regression.sh" "$PYTHON_BIN" "$RUNTIME_DIR"
"$PYTHON_BIN" "$REPO_ROOT/scripts/validate_v3120_release.py"
