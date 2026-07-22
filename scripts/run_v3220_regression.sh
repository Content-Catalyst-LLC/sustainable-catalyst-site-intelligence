#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"
python3 -m pytest -q \
  tests/test_live_intelligence_registry_discovery_v3200.py \
  tests/test_live_intelligence_registry_collections_v3210.py \
  tests/test_live_intelligence_registry_publications_v3220.py \
  tests/test_live_intelligence_registry_publications_release_contract_v3220.py
cd "$ROOT"
python3 scripts/validate_v3220_release.py
