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
from app.spatial_evidence_v2150 import SpatialEvidenceStudio  # noqa: E402


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object at the top level.")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.15.0 spatial evidence operations")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="Show the public spatial workspace summary")
    sub.add_parser("layers", help="Show the source-aware spatial layer catalog")

    areas = sub.add_parser("areas", help="List registered areas of interest")
    areas.add_argument("--public", action="store_true")

    create_area = sub.add_parser("create-area", help="Create a bounding-box, polygon, or radius area from JSON")
    create_area.add_argument("json_file", type=Path)

    datasets = sub.add_parser("datasets", help="List registered spatial datasets")
    datasets.add_argument("--public", action="store_true")
    datasets.add_argument("--all-versions", action="store_true")

    register = sub.add_parser("register", help="Register a spatial dataset from a JSON request")
    register.add_argument("json_file", type=Path)

    intersection = sub.add_parser("intersection", help="Run an area/dataset intersection")
    intersection.add_argument("area_id")
    intersection.add_argument("dataset_id")
    intersection.add_argument("--version", default="")
    intersection.add_argument("--public", action="store_true")

    proximity = sub.add_parser("proximity", help="Find spatial features near a longitude/latitude")
    proximity.add_argument("dataset_id")
    proximity.add_argument("longitude", type=float)
    proximity.add_argument("latitude", type=float)
    proximity.add_argument("--distance-km", type=float, default=100.0)
    proximity.add_argument("--version", default="")
    proximity.add_argument("--public", action="store_true")

    aggregate = sub.add_parser("aggregate", help="Aggregate intersecting features inside an area")
    aggregate.add_argument("area_id")
    aggregate.add_argument("dataset_id")
    aggregate.add_argument("--metric", default="")
    aggregate.add_argument("--version", default="")
    aggregate.add_argument("--public", action="store_true")

    compare = sub.add_parser("compare", help="Compare two versions of a spatial dataset")
    compare.add_argument("dataset_id")
    compare.add_argument("previous_version_id")
    compare.add_argument("current_version_id")
    compare.add_argument("--metric", default="")
    compare.add_argument("--public", action="store_true")

    export = sub.add_parser("export", help="Export a spatial evidence packet")
    export.add_argument("area_id")
    export.add_argument("dataset_id")
    export.add_argument("--version", default="")
    export.add_argument("--public", action="store_true")
    export.add_argument("--output", type=Path)

    args = parser.parse_args()
    studio = SpatialEvidenceStudio(Settings())

    if args.command == "summary":
        result = studio.public_summary()
    elif args.command == "layers":
        result = studio.layers()
    elif args.command == "areas":
        result = studio.areas(public=args.public)
    elif args.command == "create-area":
        result = studio.create_area(load_json(args.json_file))
    elif args.command == "datasets":
        result = studio.datasets(public=args.public, latest_only=not args.all_versions)
    elif args.command == "register":
        result = studio.register_dataset(load_json(args.json_file))
    elif args.command == "intersection":
        result = studio.intersection(args.area_id, args.dataset_id, args.version, public=args.public)
    elif args.command == "proximity":
        result = studio.proximity(
            args.dataset_id,
            args.longitude,
            args.latitude,
            args.distance_km,
            args.version,
            public=args.public,
        )
    elif args.command == "aggregate":
        result = studio.aggregate(args.area_id, args.dataset_id, args.metric, args.version, public=args.public)
    elif args.command == "compare":
        result = studio.compare(
            args.dataset_id,
            args.previous_version_id,
            args.current_version_id,
            args.metric,
            public=args.public,
        )
    else:
        result = studio.export_evidence(args.area_id, args.dataset_id, args.version, public=args.public)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(str(args.output))
            return 0

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
