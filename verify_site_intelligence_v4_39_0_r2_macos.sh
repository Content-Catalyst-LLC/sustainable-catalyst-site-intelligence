#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

"$PYTHON" "$ROOT/scripts/validate_v4390_r2_release_contract.py"
SC_SI_SKIP_TESTS="${SC_SI_SKIP_TESTS:-0}" bash "$ROOT/verify_site_intelligence_v4_39_0_r1_macos.sh"

echo "SUCCESS: Site Intelligence v4.39.0 R2 passed compact layout, capability truth, imagery, ticker, manifest, syntax, and available runtime validation."
