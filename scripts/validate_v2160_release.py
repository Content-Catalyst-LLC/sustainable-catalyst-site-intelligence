#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.16.0"', 'RELEASE_NAME = "Statistical Harmonization and Comparable-Series Engine"'],
    "backend/app/config.py": ["statistical_harmonization_enabled", "statistical_harmonization_series_index_path", "statistical_harmonization_unit_registry_path"],
    "backend/app/statistical_harmonization_v2160.py": ['RELEASE_VERSION = "2.16.0"', 'SCHEMA_VERSION = "sc-site-intelligence-statistical-harmonization/1.0"', "def register_series(", "def transform(", "def compare(", "def export(", "def workbench_handoff("],
    "backend/app/main.py": ['"/public/harmonization"', '"/public/harmonization/standards"', '"/public/harmonization/compare"', '"/admin/harmonization/control-center"', '"/admin/harmonization/transform"', '"/admin/harmonization/workbench-handoff"'],
    "backend/data/statistical_harmonization_policy_v2160.json": ['"version": "2.16.0"', '"silent_normalization": false', '"silent_imputation": false', '"automatic_rankings": false'],
    "backend/data/unit_registry_v2160.json": ['"code":"percent"', '"code":"currency"', '"code":"USD"'],
    "backend/public_app/index.html": ['data-route="harmonization"', 'id="harmonizationStudio"', '/app/assets/harmonization-v2160.js?v=2.16.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.16.0"', 'harmonization:[', 'window.SCHarmonizationV2160'],
    "backend/public_app/assets/harmonization-v2160.js": ['const VERSION="2.16.0"', 'window.SCHarmonizationV2160', '/public/harmonization/compare'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.16.0"', '"/app/assets/harmonization-v2160.css"', '"/app/assets/harmonization-v2160.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.16.0', 'sc_public_comparable_series', 'sc_statistical_harmonization_control_center', 'public-comparable-series'],
    "scripts/statistical_harmonization_v2160.py": ["register", "transform", "compare", "export"],
    "docs/V2160_STATISTICAL_HARMONIZATION_COMPARABLE_SERIES_ENGINE.md": ["Dimension-checked unit conversion", "No silent normalization", "Workbench"],
    "docs/RELEASE_MANIFEST_V2160.json": ['"release": "2.16.0"', '"silent_normalization": false', '"automatic_rankings": false'],
    "README.md": ["Current release:** v2.16.0 — Statistical Harmonization and Comparable-Series Engine", "/app/?view=harmonization"],
    "CHANGELOG.md": ["## 2.16.0 — Statistical Harmonization and Comparable-Series Engine"],
}
for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")
manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2160.json").read_text())
if manifest.get("silent_normalization") is not False or manifest.get("silent_imputation") is not False:
    raise SystemExit("Harmonization release must prohibit hidden normalization and imputation.")
if manifest.get("automatic_rankings") is not False or manifest.get("implicit_exchange_rates") is not False:
    raise SystemExit("Harmonization release must prohibit rankings and implicit exchange rates.")
runtime = ROOT / "backend/data/statistical_harmonization_v2160"
if runtime.exists():
    raise SystemExit("Writable harmonization state must not be packaged.")
for path in ROOT.rglob("*"):
    if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
        raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")
print("Site Intelligence v2.16.0 release contract passed.")
