#!/usr/bin/env python3
"""Run a mandatory browser gate with bounded teardown and one clean retry."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_browser_gate_v32363.py <gate-script>", file=sys.stderr)
        return 2
    target = (ROOT / "scripts" / sys.argv[1]).resolve()
    if not target.is_file() or target.parent != (ROOT / "scripts").resolve():
        print("ERROR: browser gate script is missing or outside the release scripts directory.", file=sys.stderr)
        return 2
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "backend")
    last_output = ""
    for attempt in (1, 2):
        process = subprocess.Popen(
            [sys.executable, str(target)],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            output, _ = process.communicate(timeout=75)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                output, _ = process.communicate()
            last_output = output or ""
            print(last_output, end="")
            print(f"Browser gate attempt {attempt} exceeded 75 seconds; retrying with a clean process." if attempt == 1 else "ERROR: browser gate did not complete after two bounded attempts.", file=sys.stderr)
            continue
        last_output = output or ""
        print(last_output, end="")
        if process.returncode == 0:
            return 0
        if attempt == 1:
            print("Browser gate failed once; retrying with a clean process.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
