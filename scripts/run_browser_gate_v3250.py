#!/usr/bin/env python3
"""Run a mandatory browser gate with bounded teardown and one clean retry."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def terminate_group(process: subprocess.Popen[object]) -> None:
    """Remove browser descendants without depending on captured-pipe EOF."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        return


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_browser_gate_v3250.py <gate-script>", file=sys.stderr)
        return 2
    target = (ROOT / "scripts" / sys.argv[1]).resolve()
    if not target.is_file() or target.parent != (ROOT / "scripts").resolve():
        print("ERROR: browser gate script is missing or outside the release scripts directory.", file=sys.stderr)
        return 2
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "backend")
    for attempt in (1, 2):
        output_path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="scsi-browser-gate-", suffix=".log", delete=False) as output_file:
                output_path = Path(output_file.name)
                process = subprocess.Popen(
                    [sys.executable, str(target)],
                    cwd=ROOT,
                    env=env,
                    stdout=output_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    return_code = process.wait(timeout=75)
                except subprocess.TimeoutExpired:
                    terminate_group(process)
                    try:
                        return_code = process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        return_code = process.wait()
                    timed_out = True
                else:
                    timed_out = False
                    # The gate process is complete. Clean any Chromium descendants
                    # that outlived Playwright so they cannot retain resources.
                    terminate_group(process)
            output = output_path.read_text(encoding="utf-8", errors="replace") if output_path else ""
            print(output, end="")
            if not timed_out and return_code == 0:
                return 0
            if timed_out:
                message = (
                    f"Browser gate attempt {attempt} exceeded 75 seconds; retrying with a clean process."
                    if attempt == 1
                    else "ERROR: browser gate did not complete after two bounded attempts."
                )
                print(message, file=sys.stderr)
            elif attempt == 1:
                print("Browser gate failed once; retrying with a clean process.", file=sys.stderr)
        finally:
            if output_path is not None:
                output_path.unlink(missing_ok=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
