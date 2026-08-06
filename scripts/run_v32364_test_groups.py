#!/usr/bin/env python3
"""Run the complete pytest inventory in bounded process-isolated groups.

A small number of inherited FastAPI and connector tests can finish successfully
but leave a helper thread or process alive during interpreter shutdown. This
runner never waits indefinitely: every test file is collected exactly once,
each group has a hard timeout, and a timed-out process is accepted only when
pytest already emitted an unambiguous all-passed summary for that group.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PYTHON = os.environ.get("PYTHON") or sys.executable
BATCH_SIZE = 20
GROUP_TIMEOUT_SECONDS = 60


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


def collect_inventory(runtime_root: Path) -> tuple[int, list[Path]]:
    result = subprocess.run(
        [PYTHON, "-m", "pytest", "--collect-only", "-q", "backend/tests"],
        cwd=ROOT,
        env=environment(runtime_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=90,
    )
    if result.returncode:
        print(result.stdout, end="")
        raise SystemExit("ERROR: pytest collection failed.")
    match = re.search(r"(\d+) tests collected", result.stdout)
    count = int(match.group(1)) if match else 0
    files = sorted((BACKEND / "tests").glob("test_*.py"))
    if count <= 0 or not files:
        print(result.stdout, end="")
        raise SystemExit("ERROR: pytest inventory is empty or incomplete.")
    return count, files


def completed_pass(output: str) -> bool:
    lowered = output.lower()
    return bool(re.search(r"\b\d+ passed\b", lowered)) and not any(
        token in lowered for token in (" failed", " error", " interrupted", " traceback")
    )


def run_group(command: list[str], runtime_root: Path) -> tuple[int, str, bool]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment(runtime_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=GROUP_TIMEOUT_SECONDS)
        return int(process.returncode or 0), output or "", False
    except subprocess.TimeoutExpired as exc:
        partial = exc.output or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        if process.stdout is not None:
            try:
                process.stdout.close()
            except Exception:
                pass
        return 124, partial, True


def main() -> int:
    base = Path(os.environ.get("SC_SI_RUNTIME_STATE_ROOT") or tempfile.mkdtemp(prefix="scsi-v32364-tests-"))
    base.mkdir(parents=True, exist_ok=True)
    count, files = collect_inventory(base / "collect")
    batches = [files[start : start + BATCH_SIZE] for start in range(0, len(files), BATCH_SIZE)]

    for index, batch in enumerate(batches, start=1):
        start = (index - 1) * BATCH_SIZE + 1
        end = start + len(batch) - 1
        print(f"\n==> Test group {index}/{len(batches)}: files {start}-{end} of {len(files)}", flush=True)
        runtime = base / f"group-{index:02d}"
        runtime.mkdir(parents=True, exist_ok=True)
        relative = [str(path.relative_to(ROOT)) for path in batch]
        returncode, output, timed_out = run_group(
            [PYTHON, "-m", "pytest", "-q", "--disable-warnings", *relative],
            runtime,
        )
        print(output, end="", flush=True)
        if timed_out and completed_pass(output):
            print(
                "PASS: pytest reported a complete group pass; a lingering cleanup process was terminated.",
                flush=True,
            )
            continue
        if timed_out:
            raise SystemExit(
                f"ERROR: test group {index} exceeded {GROUP_TIMEOUT_SECONDS} seconds before a complete pass summary."
            )
        if returncode:
            raise SystemExit(f"ERROR: test group {index} failed; first file: {relative[0]}")

    print(f"\nPASS: all {count} collected tests passed across {len(batches)} bounded groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
