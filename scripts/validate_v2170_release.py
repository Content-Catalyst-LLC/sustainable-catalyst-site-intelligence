#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ['APP_VERSION = "2.17.0"', 'RELEASE_NAME = "Model Registry, Forecast Evaluation, and Early-Warning Indicators"'],
    "backend/app/config.py": ["model_governance_enabled", "model_governance_models_path", "model_governance_warning_events_path"],
    "backend/app/model_forecast_early_warning_v2170.py": ['RELEASE_VERSION = "2.17.0"', 'SCHEMA_VERSION = "sc-site-intelligence-model-forecast-governance/1.0"', "def register_model(", "def ingest_forecast(", "def evaluate_forecast(", "def register_warning_rule(", "def evaluate_warning(", "def export_governance_packet("],
    "backend/app/main.py": ['"/public/model-governance"', '"/public/model-governance/methodology"', '"/public/models"', '"/public/forecasts"', '"/public/forecast-evaluations"', '"/public/early-warning"', '"/admin/model-governance/control-center"'],
    "backend/data/model_governance_policy_v2170.json": ['"version": "2.17.0"', "No individual-level targeting", "No hidden model substitution", "No autonomous legal"],
    "backend/data/model_metric_registry_v2170.json": ['"code": "mae"', '"code": "rmse"', '"code": "calibration_gap"', '"code": "drift_ratio"'],
    "backend/public_app/index.html": ['data-route="models"', 'id="modelGovernanceStudio"', '/app/assets/models-v2170.js?v=2.17.0'],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.17.0"', 'models:[', 'window.SCModelsV2170'],
    "backend/public_app/assets/models-v2170.js": ['const VERSION="2.17.0"', 'window.SCModelsV2170', '/public/model-governance'],
    "backend/public_app/service-worker.js": ['const RELEASE="2.17.0"', '"/app/assets/models-v2170.css"', '"/app/assets/models-v2170.js"'],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ['Version: 2.17.0', 'sc_public_model_forecasts', 'sc_model_forecast_control_center', 'public-model-forecasts'],
    "scripts/model_governance_v2170.py": ["register-model", "ingest-forecast", "evaluate-forecast", "register-warning", "evaluate-warning", "export"],
    "docs/V2170_MODEL_REGISTRY_FORECAST_EVALUATION_EARLY_WARNING.md": ["Versioned statistical", "mean absolute error", "No individual-level data", "review signal only"],
    "docs/RELEASE_MANIFEST_V2170.json": ['"release": "2.17.0"', '"automatic_decision_authority": false', '"individual_targeting": false', '"forecast_scenario_substitution": false'],
    "README.md": ["Current release:** v2.17.0 — Model Registry, Forecast Evaluation, and Early-Warning Indicators", "/app/?view=models"],
    "CHANGELOG.md": ["## 2.17.0 — Model Registry, Forecast Evaluation, and Early-Warning Indicators"],
}
for relative, markers in CHECKS.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing release marker {marker!r} in {relative}")
manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2170.json").read_text())
for key in ["automatic_decision_authority", "individual_targeting", "emergency_dispatch_authority", "forecast_scenario_substitution", "silent_retraining", "guaranteed_outcomes"]:
    if manifest.get(key) is not False:
        raise SystemExit(f"Model governance boundary must remain false: {key}")
runtime = ROOT / "backend/data/model_governance_v2170"
if runtime.exists():
    raise SystemExit("Writable model-governance state must not be packaged.")
for path in ROOT.rglob("*"):
    if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
        raise SystemExit(f"Generated cache directory must not be packaged: {path.relative_to(ROOT)}")
print("Site Intelligence v2.17.0 release contract passed.")
