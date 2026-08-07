#!/usr/bin/env python3
"""Run the complete pytest inventory in bounded, file-backed process groups.

Some inherited connector tests can report a complete pass but retain an executor
thread during interpreter shutdown. Capturing those processes through a pipe can
also keep the parent validator blocked because a descendant retains the pipe.
This runner writes each group's output to a temporary file, imposes a hard
process-group timeout, and accepts a terminated teardown only when pytest has
already emitted an unambiguous all-passed summary for that exact group.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PYTHON = os.environ.get("PYTHON") or sys.executable
BATCH_SIZE = 10
GROUP_TIMEOUT_SECONDS = 40
COLLECT_TIMEOUT_SECONDS = 90


def environment(runtime_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": str(BACKEND),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "SC_SI_RUNTIME_STATE_ROOT": str(runtime_root),
        }
    )
    return env


def run_file_backed(
    command: list[str], runtime_root: Path, timeout_seconds: int, output_path: Path
) -> tuple[int, str, bool]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment(runtime_root),
            text=True,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        deadline = time.monotonic() + timeout_seconds
        summary_seen_at: float | None = None
        terminated_after_summary = False
        exceeded_deadline = False
        while True:
            returncode = process.poll()
            try:
                current_output = output_path.read_text(encoding="utf-8")
            except (FileNotFoundError, UnicodeDecodeError):
                current_output = ""
            if returncode is not None:
                break
            if completed_pass(current_output):
                if summary_seen_at is None:
                    summary_seen_at = time.monotonic()
                elif time.monotonic() - summary_seen_at >= 2.0:
                    terminated_after_summary = True
                    break
            if time.monotonic() >= deadline:
                exceeded_deadline = True
                break
            time.sleep(0.2)
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            for _ in range(25):
                if process.poll() is not None:
                    break
                time.sleep(0.2)
            if process.poll() is None:
                process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    try:
        output = output_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        output = ""
    interrupted = terminated_after_summary or exceeded_deadline
    return int(process.returncode or 0), output, interrupted


def passed_count(output: str) -> int:
    matches = re.findall(r"(?:^|\s)(\d+) passed\b", output.lower())
    return int(matches[-1]) if matches else 0


def completed_pass(output: str) -> bool:
    lowered = output.lower()
    return passed_count(output) > 0 and not any(
        token in lowered
        for token in (
            " failed",
            " error",
            " interrupted",
            " traceback",
            " keyboardinterrupt",
        )
    )


def collect_inventory(runtime_root: Path, output_dir: Path) -> tuple[int, list[Path]]:
    returncode, output, timed_out = run_file_backed(
        [PYTHON, "-m", "pytest", "--collect-only", "-q", "backend/tests"],
        runtime_root,
        COLLECT_TIMEOUT_SECONDS,
        output_dir / "collection.txt",
    )
    if timed_out or returncode:
        print(output, end="", flush=True)
        raise SystemExit("ERROR: pytest collection failed or exceeded its timeout.")
    match = re.search(r"(\d+) tests collected", output)
    count = int(match.group(1)) if match else 0
    files = sorted((BACKEND / "tests").glob("test_*.py"))
    if count <= 0 or not files:
        print(output, end="", flush=True)
        raise SystemExit("ERROR: pytest inventory is empty or incomplete.")
    return count, files


def main() -> int:
    base = Path(
        os.environ.get("SC_SI_RUNTIME_STATE_ROOT")
        or tempfile.mkdtemp(prefix="scsi-v3260-tests-")
    )
    base.mkdir(parents=True, exist_ok=True)
    output_dir = base / "pytest-output"
    count, files = collect_inventory(base / "collect", output_dir)
    batches = [files[start : start + BATCH_SIZE] for start in range(0, len(files), BATCH_SIZE)]
    passed_total = 0

    for index, batch in enumerate(batches, start=1):
        start = (index - 1) * BATCH_SIZE + 1
        end = start + len(batch) - 1
        print(
            f"\n==> Test group {index}/{len(batches)}: files {start}-{end} of {len(files)}",
            flush=True,
        )
        runtime = base / f"group-{index:02d}"
        runtime.mkdir(parents=True, exist_ok=True)
        relative = [str(path.relative_to(ROOT)) for path in batch]
        returncode, output, timed_out = run_file_backed(
            [PYTHON, "-m", "pytest", "-q", "--disable-warnings", *relative],
            runtime,
            GROUP_TIMEOUT_SECONDS,
            output_dir / f"group-{index:02d}.txt",
        )
        print(output, end="", flush=True)
        group_passed = passed_count(output)
        if timed_out and completed_pass(output):
            print(
                "PASS: pytest reported a complete group pass; lingering teardown was terminated.",
                flush=True,
            )
            passed_total += group_passed
            continue
        if timed_out:
            raise SystemExit(
                f"ERROR: test group {index} exceeded {GROUP_TIMEOUT_SECONDS} seconds before a complete pass summary."
            )
        if returncode:
            raise SystemExit(f"ERROR: test group {index} failed; first file: {relative[0]}")
        if not completed_pass(output):
            raise SystemExit(f"ERROR: test group {index} exited without a complete pass summary.")
        passed_total += group_passed

    if passed_total != count:
        raise SystemExit(
            f"ERROR: pytest reported {passed_total} passed tests, but collection found {count}."
        )
    print(
        f"\nPASS: all {count} collected tests passed across {len(batches)} bounded file-backed groups.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
