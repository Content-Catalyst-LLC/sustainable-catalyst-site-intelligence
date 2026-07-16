#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import Settings  # noqa: E402
from app.model_forecast_early_warning_v2170 import ModelForecastEarlyWarningCenter  # noqa: E402


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.17.0 model, forecast, evaluation, and early-warning operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("methodology")
    sub.add_parser("diagnostics")
    models = sub.add_parser("models")
    models.add_argument("--public", action="store_true")
    register = sub.add_parser("register-model")
    register.add_argument("json_file", type=Path)
    forecasts = sub.add_parser("forecasts")
    forecasts.add_argument("--model-id", default="")
    forecasts.add_argument("--public", action="store_true")
    ingest = sub.add_parser("ingest-forecast")
    ingest.add_argument("json_file", type=Path)
    evaluations = sub.add_parser("evaluations")
    evaluations.add_argument("--model-id", default="")
    evaluations.add_argument("--public", action="store_true")
    evaluate = sub.add_parser("evaluate-forecast")
    evaluate.add_argument("json_file", type=Path)
    warnings = sub.add_parser("warnings")
    warnings.add_argument("--public", action="store_true")
    register_warning = sub.add_parser("register-warning")
    register_warning.add_argument("json_file", type=Path)
    evaluate_warning = sub.add_parser("evaluate-warning")
    evaluate_warning.add_argument("json_file", type=Path)
    export = sub.add_parser("export")
    export.add_argument("model_id")
    export.add_argument("--version", default="")
    export.add_argument("--public", action="store_true")
    export.add_argument("--output", type=Path)
    args = parser.parse_args()

    center = ModelForecastEarlyWarningCenter(Settings())
    if args.command == "summary":
        result = center.public_summary()
    elif args.command == "methodology":
        result = center.methodology()
    elif args.command == "diagnostics":
        result = center.diagnostics()
    elif args.command == "models":
        result = center.models(public=args.public)
    elif args.command == "register-model":
        result = center.register_model(load_json(args.json_file))
    elif args.command == "forecasts":
        result = center.forecasts(public=args.public, model_id=args.model_id)
    elif args.command == "ingest-forecast":
        result = center.ingest_forecast(load_json(args.json_file))
    elif args.command == "evaluations":
        result = center.evaluations(public=args.public, model_id=args.model_id)
    elif args.command == "evaluate-forecast":
        result = center.evaluate_forecast(load_json(args.json_file))
    elif args.command == "warnings":
        result = center.warning_summary(public=args.public)
    elif args.command == "register-warning":
        result = center.register_warning_rule(load_json(args.json_file))
    elif args.command == "evaluate-warning":
        result = center.evaluate_warning(load_json(args.json_file))
    else:
        result = center.export_governance_packet(args.model_id, args.version, public=args.public)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(args.output)
            return 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
