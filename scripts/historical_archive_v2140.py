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
from app.historical_archive_v2140 import HistoricalArchiveCenter  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.14.0 historical archive operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("datasets", help="List historical dataset coverage")
    list_parser.add_argument("--private", action="store_true", help="Include private storage metadata")

    snapshots_parser = subparsers.add_parser("snapshots", help="List snapshot metadata")
    snapshots_parser.add_argument("--dataset", default="")
    snapshots_parser.add_argument("--connector", default="")
    snapshots_parser.add_argument("--limit", type=int, default=100)

    capture_parser = subparsers.add_parser("capture", help="Capture a manual JSON snapshot")
    capture_parser.add_argument("dataset_id")
    capture_parser.add_argument("connector_id")
    capture_parser.add_argument("json_file", type=Path)
    capture_parser.add_argument("--source-timestamp", default="")
    capture_parser.add_argument("--source-revision", default="")
    capture_parser.add_argument("--force", action="store_true")

    export_parser = subparsers.add_parser("export", help="Export a dataset history bundle")
    export_parser.add_argument("dataset_id")
    export_parser.add_argument("--include-payloads", action="store_true")
    export_parser.add_argument("--output", type=Path)

    retention_parser = subparsers.add_parser("retention", help="Preview or apply retention")
    retention_parser.add_argument("--dataset", default="")
    retention_parser.add_argument("--days", type=int)
    retention_parser.add_argument("--max-snapshots", type=int)
    retention_parser.add_argument("--apply", action="store_true")

    args = parser.parse_args()
    center = HistoricalArchiveCenter(Settings())
    if args.command == "datasets":
        result = center.datasets(public=not args.private)
    elif args.command == "snapshots":
        result = center.snapshots(dataset_id=args.dataset, connector_id=args.connector, limit=args.limit, public=False)
    elif args.command == "capture":
        payload = json.loads(args.json_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SystemExit("Snapshot JSON must contain an object at the top level.")
        result = center.capture_snapshot(
            dataset_id=args.dataset_id,
            connector_id=args.connector_id,
            payload=payload,
            source_timestamp=args.source_timestamp,
            source_revision_id=args.source_revision,
            force=args.force,
        )
    elif args.command == "export":
        result = center.export_bundle(args.dataset_id, include_payloads=args.include_payloads)
        if args.output:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(str(args.output))
            return 0
    else:
        result = center.retention(
            dry_run=not args.apply,
            dataset_id=args.dataset,
            retention_days=args.days,
            max_snapshots=args.max_snapshots,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
