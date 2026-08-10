#!/usr/bin/env python3
"""Run the complete v4.12.0 test inventory in one file-backed process.

The full inventory completes faster and more deterministically as one pytest process.
Output is written to a file so descendants cannot retain the validator's stdout pipe;
a complete all-passed summary is accepted before bounded teardown cleanup.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

from run_v3280_test_groups import completed_pass, passed_count, run_file_backed

ROOT = Path(__file__).resolve().parents[1]
PYTHON = os.environ.get("PYTHON") or sys.executable


def main() -> int:
    base = Path(os.environ.get("SC_SI_RUNTIME_STATE_ROOT") or tempfile.mkdtemp(prefix="scsi-v3280-tests-"))
    base.mkdir(parents=True, exist_ok=True)
    collection_path = base / "pytest-collection.txt"
    rc, collection, interrupted = run_file_backed(
        [PYTHON, "-m", "pytest", "--collect-only", "-q", "backend/tests"],
        base / "collect-runtime",
        90,
        collection_path,
    )
    match = re.search(r"(\d+) tests collected", collection)
    expected = int(match.group(1)) if match else 0
    if rc or interrupted or expected <= 0:
        print(collection, end="")
        raise SystemExit("ERROR: complete pytest inventory could not be collected.")

    output_path = base / "pytest-complete.txt"
    rc, output, interrupted = run_file_backed(
        [PYTHON, "-m", "pytest", "-q", "--disable-warnings", "backend/tests"],
        base / "suite-runtime",
        90,
        output_path,
    )
    print(output, end="", flush=True)
    actual = passed_count(output)
    if not completed_pass(output) or actual != expected:
        raise SystemExit(f"ERROR: complete test suite reported {actual} passes for {expected} collected tests.")
    if rc and not interrupted:
        raise SystemExit(f"ERROR: pytest exited with status {rc}.")
    if interrupted:
        print("PASS: complete pytest summary was recorded; lingering teardown was terminated.")
    print(f"PASS: all {actual} collected tests passed in the complete file-backed suite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
