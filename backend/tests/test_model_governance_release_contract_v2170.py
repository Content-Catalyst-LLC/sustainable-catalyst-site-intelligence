from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_files_and_markers():
    checks = {
        "backend/app/version.py": ['APP_VERSION = "3.20.0"', 'RELEASE_NAME = "Connected Public Intelligence and Evidence Platform"'],
        "backend/app/config.py": ["model_governance_enabled", "model_governance_forecasts_path", "model_governance_warning_events_path"],
        "backend/app/model_forecast_early_warning_v2170.py": ['RELEASE_VERSION = "3.20.0"', "def register_model(", "def ingest_forecast(", "def evaluate_forecast(", "def evaluate_warning("],
        "backend/app/main.py": ['"/public/model-governance"', '"/public/models"', '"/public/forecast-evaluations"', '"/public/early-warning"', '"/admin/model-governance/control-center"'],
        "backend/data/model_governance_policy_v2170.json": ['"version": "3.20.0"', "No individual-level targeting", "No hidden model substitution"],
        "backend/data/model_metric_registry_v2170.json": ['"code": "mae"', '"code": "calibration_gap"', '"code": "drift_ratio"'],
        "README.md": ["Current release:** v3.20.0 — Connected Public Intelligence and Evidence Platform"],
        "CHANGELOG.md": ["## 2.17.0 — Model Registry, Forecast Evaluation, and Early-Warning Indicators"],
    }
    for relative, markers in checks.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, (relative, marker)


def test_writable_model_state_is_not_packaged():
    assert not (ROOT / "backend/data/model_governance_v2170").exists()
