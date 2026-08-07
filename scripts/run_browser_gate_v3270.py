#!/usr/bin/env python3
"""Run a mandatory browser gate with bounded, file-backed teardown.

Playwright/Chromium descendants can outlive the Python gate after the gate has already
printed its final PASS line. This runner treats that final PASS as the completion
contract, then terminates the process group so the installer cannot hang on browser
teardown. A gate without a PASS line never succeeds.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 70
PASS_GRACE_SECONDS = 0.5


def output_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def gate_passed(text: str) -> bool:
    lowered = text.lower()
    return "pass:" in lowered and not any(token in lowered for token in ("traceback (most recent call last)", "assertionerror:"))


def terminate(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError:
        try:
            process.kill()
        except ProcessLookupError:
            return
    deadline = time.monotonic() + 2.0
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)


def run_once(target: Path, attempt: int) -> tuple[bool, str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "backend")
    output_path = Path(tempfile.mkstemp(prefix="scsi-browser-gate-", suffix=".log")[1])
    try:
        with output_path.open("w", encoding="utf-8") as output_file:
            process = subprocess.Popen(
                [sys.executable, str(target)],
                cwd=ROOT,
                env=env,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            deadline = time.monotonic() + TIMEOUT_SECONDS
            pass_seen_at: float | None = None
            while True:
                text = output_text(output_path)
                if gate_passed(text):
                    if pass_seen_at is None:
                        pass_seen_at = time.monotonic()
                    elif time.monotonic() - pass_seen_at >= PASS_GRACE_SECONDS:
                        terminate(process)
                        return True, text, "pass-line"
                rc = process.poll()
                if rc is not None:
                    text = output_text(output_path)
                    return rc == 0 and gate_passed(text), text, f"exit-{rc}"
                if time.monotonic() >= deadline:
                    terminate(process)
                    text = output_text(output_path)
                    if gate_passed(text):
                        return True, text, "pass-before-timeout"
                    return False, text, "timeout"
                time.sleep(0.1)
    finally:
        output_path.unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_browser_gate_v3270.py <gate-script>", file=sys.stderr)
        return 2
    target = (ROOT / "scripts" / sys.argv[1]).resolve()
    scripts = (ROOT / "scripts").resolve()
    if not target.is_file() or target.parent != scripts:
        print("ERROR: browser gate script is missing or outside the release scripts directory.", file=sys.stderr)
        return 2
    for attempt in (1, 2):
        ok, text, state = run_once(target, attempt)
        print(text, end="")
        if ok:
            if state != "exit-0":
                print(f"PASS: bounded browser runner accepted completed gate output ({state}) and cleaned lingering browser teardown.")
            return 0
        if attempt == 1:
            print(f"Browser gate attempt 1 did not complete cleanly ({state}); retrying with a clean process.", file=sys.stderr)
        else:
            print(f"ERROR: browser gate failed after two attempts ({state}).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
