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
from app.statistical_harmonization_v2160 import StatisticalHarmonizationEngine  # noqa: E402


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.16.0 statistical harmonization operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("standards")
    sub.add_parser("methodology")
    series = sub.add_parser("series")
    series.add_argument("--public", action="store_true")
    register = sub.add_parser("register")
    register.add_argument("json_file", type=Path)
    transform = sub.add_parser("transform")
    transform.add_argument("json_file", type=Path)
    compare = sub.add_parser("compare")
    compare.add_argument("json_file", type=Path)
    compare.add_argument("--public", action="store_true")
    export = sub.add_parser("export")
    export.add_argument("series_id")
    export.add_argument("--version", default="")
    export.add_argument("--public", action="store_true")
    export.add_argument("--output", type=Path)
    args = parser.parse_args()
    engine = StatisticalHarmonizationEngine(Settings())
    if args.command == "summary": result = engine.public_summary()
    elif args.command == "standards": result = engine.standards()
    elif args.command == "methodology": result = engine.methodology()
    elif args.command == "series": result = engine.series(public=args.public)
    elif args.command == "register": result = engine.register_series(load_json(args.json_file))
    elif args.command == "transform": result = engine.transform(load_json(args.json_file))
    elif args.command == "compare": result = engine.compare(load_json(args.json_file), public=args.public)
    else:
        result = engine.export(args.series_id, args.version, public=args.public)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(args.output)
            return 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
