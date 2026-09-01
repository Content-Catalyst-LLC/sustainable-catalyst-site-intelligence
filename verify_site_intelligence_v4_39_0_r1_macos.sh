#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

"$PYTHON" "$ROOT/scripts/validate_v4390_r1_release_contract.py"
SC_SI_SKIP_TESTS="${SC_SI_SKIP_TESTS:-0}" bash "$ROOT/verify_site_intelligence_v4_39_0_macos.sh"

echo "SUCCESS: Site Intelligence v4.39.0 R1 passed visual console, imagery, original ticker, manifest, syntax, and available runtime validation."
