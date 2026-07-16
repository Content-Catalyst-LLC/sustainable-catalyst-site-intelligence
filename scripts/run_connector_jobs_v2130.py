#!/usr/bin/env python3
"""Explicit v2.13.0 connector due-job runner for local, CI, or external schedulers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import Settings  # noqa: E402
from app.connector_operations_v2130 import ConnectorOperationsCenter  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Site Intelligence connector jobs that are currently due.")
    parser.add_argument("--live", action="store_true", help="Perform live connector calls. Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Override quota and open-circuit checks where supported.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum number of due jobs to execute (1-100).")
    args = parser.parse_args()
    settings = Settings()
    center = ConnectorOperationsCenter(settings)
    result = center.run_due_jobs(dry_run=not args.live, force=args.force, limit=args.limit)
    print(json.dumps(result, indent=2, sort_keys=True))
    failed = sum(result.get("status_counts", {}).get(status, 0) for status in ("failed", "quarantined", "blocked"))
    return 1 if args.live and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
