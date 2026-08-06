#!/usr/bin/env python3
"""Run the complete pytest inventory with adaptive process isolation.

Some inherited TestClient combinations complete their assertions but leave a
non-daemon teardown thread behind. This runner never treats a hung process as a
pass: it recursively splits timed-out batches until every test file exits with
status zero in an isolated process.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PYTHON = os.environ.get("PYTHON") or sys.executable
BATCH_SIZE = int(os.environ.get("SC_SI_TEST_BATCH_SIZE", "8"))
TIMEOUT_SECONDS = int(os.environ.get("SC_SI_TEST_BATCH_TIMEOUT", "18"))


def command(files: list[Path]) -> list[str]:
    return [PYTHON, "-m", "pytest", "-q", "--disable-warnings", *[str(path.relative_to(BACKEND)) for path in files]]


def run_batch(files: list[Path], depth: int = 0) -> None:
    label = f"{files[0].name} … {files[-1].name}" if len(files) > 1 else files[0].name
    print(f"\n{'  ' * depth}Validating {len(files)} file(s): {label}", flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    try:
        result = subprocess.run(
            command(files),
            cwd=BACKEND,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "")
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        if output:
            print(output.rstrip(), flush=True)
        if len(files) == 1:
            raise SystemExit(f"ERROR: {files[0].name} did not exit within {TIMEOUT_SECONDS} seconds.")
        midpoint = len(files) // 2
        print(f"{'  ' * depth}Batch teardown did not exit; splitting without accepting it as a pass.", flush=True)
        run_batch(files[:midpoint], depth + 1)
        run_batch(files[midpoint:], depth + 1)
        return
    print(result.stdout.rstrip(), flush=True)
    if result.returncode != 0:
        raise SystemExit(f"ERROR: pytest failed for batch beginning with {files[0].name}.")


def main() -> int:
    files = sorted((BACKEND / "tests").glob("test_*.py"))
    if not files:
        raise SystemExit("ERROR: no tests were found.")
    collect = subprocess.run(
        [PYTHON, "-m", "pytest", "--collect-only", "-q"],
        cwd=BACKEND,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONPATH": str(BACKEND), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        check=True,
    )
    match = re.search(r"(\d+) tests collected", collect.stdout)
    collected = int(match.group(1)) if match else 0
    for start in range(0, len(files), BATCH_SIZE):
        run_batch(files[start : start + BATCH_SIZE])
    print(f"\nPASS: all {collected} collected tests passed with process-isolated teardown verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
