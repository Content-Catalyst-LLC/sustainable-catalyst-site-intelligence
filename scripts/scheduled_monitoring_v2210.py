#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.config import Settings  # noqa: E402
from app.scheduled_monitoring_v2210 import ScheduledMonitoringCenter  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Site Intelligence v2.21.0 scheduled monitoring CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    sub.add_parser("diagnostics")
    sub.add_parser("control-center")
    due = sub.add_parser("run-due")
    due.add_argument("--execute", action="store_true", help="Execute due monitors instead of returning the default dry run.")
    due.add_argument("--limit", type=int, default=100)
    check = sub.add_parser("check")
    check.add_argument("monitor_id")
    digest = sub.add_parser("digest")
    digest.add_argument("--period", choices=["daily", "weekly"], default="daily")
    digest.add_argument("--monitor-id", action="append", default=[])
    digest.add_argument("--visibility", choices=["private", "unlisted", "public"], default="private")
    args = parser.parse_args()
    center = ScheduledMonitoringCenter(Settings())
    if args.command == "summary": result = center.public_summary()
    elif args.command == "diagnostics": result = center.diagnostics(public=False)
    elif args.command == "control-center": result = center.control_center()
    elif args.command == "run-due": result = center.run_due(dry_run=not args.execute, limit=args.limit)
    elif args.command == "check": result = center.check_monitor(args.monitor_id)
    else: result = center.generate_digest({"period": args.period, "monitor_ids": args.monitor_id, "visibility": args.visibility})
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
