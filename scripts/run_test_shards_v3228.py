#!/usr/bin/env python3
"""Run the complete Site Intelligence suite in isolated deterministic groups.

The inherited suite creates several TestClient/thread pools. Some combinations can
finish assertions but stall interpreter shutdown. This runner disables unrelated
third-party pytest plugins, emits progress heartbeats, and automatically bisects
any stalled group. Every test file remains fail-closed and runs in a fresh process.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def run_group(files: list[Path], *, python: str, label: str, timeout_seconds: int) -> int:
    with tempfile.TemporaryDirectory(prefix=f"scsi-v3228-{label}-") as runtime:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BACKEND)
        env["SC_SI_RUNTIME_STATE_ROOT"] = runtime
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        command = [python, "-m", "pytest", "-q", "--disable-warnings", *[str(p.relative_to(BACKEND)) for p in files]]
        print(f"\n==> Test group {label}: {len(files)} files", flush=True)
        output_path = Path(runtime) / "pytest-output.txt"
        started = time.monotonic()
        with output_path.open("w", encoding="utf-8") as output_file:
            process = subprocess.Popen(
                command,
                cwd=BACKEND,
                env=env,
                text=True,
                stdout=output_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            next_heartbeat = started + 8
            timed_out = False
            while process.poll() is None:
                now = time.monotonic()
                if now - started >= timeout_seconds:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                    break
                if now >= next_heartbeat:
                    print(f"... group {label} still running ({int(now-started)}s)", flush=True)
                    next_heartbeat = now + 8
                time.sleep(0.25)
        output = output_path.read_text(encoding="utf-8", errors="replace")
        if timed_out:
            if output:
                print(output, end="")
            if len(files) == 1:
                print(f"ERROR: {files[0].name} exceeded {timeout_seconds}s.", flush=True)
                return -1
            midpoint = len(files) // 2
            print(f"NOTICE: group {label} stalled; retrying as two isolated subgroups.", flush=True)
            left = run_group(files[:midpoint], python=python, label=f"{label}a", timeout_seconds=timeout_seconds)
            if left < 0:
                return -1
            right = run_group(files[midpoint:], python=python, label=f"{label}b", timeout_seconds=timeout_seconds)
            if right < 0:
                return -1
            return left + right
        print(output, end="")
        if process.returncode:
            return -1
        matches = re.findall(r"(\d+) passed", output)
        if not matches:
            print(f"ERROR: unable to determine passing-test count for group {label}.", flush=True)
            return -1
        generated = BACKEND / "backend"
        if generated.exists():
            shutil.rmtree(generated)
        return int(matches[-1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=int, default=6)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--only-shard", type=int, default=0, help="Run one 1-indexed top-level shard for package verification.")
    args = parser.parse_args()
    files = sorted((BACKEND / "tests").glob("test_*.py"))
    if not files:
        raise SystemExit("No tests found.")
    shard_count = max(1, min(args.shards, len(files)))
    base, extra = divmod(len(files), shard_count)
    shards: list[list[Path]] = []
    start = 0
    for index in range(shard_count):
        size = base + (1 if index < extra else 0)
        shards.append(files[start:start + size])
        start += size
    selected = list(enumerate(shards, 1))
    if args.only_shard:
        if args.only_shard < 1 or args.only_shard > len(shards):
            raise SystemExit(f"--only-shard must be between 1 and {len(shards)}")
        selected = [(args.only_shard, shards[args.only_shard - 1])]
    passed_total = 0
    selected_files = 0
    for index, shard in selected:
        passed = run_group(shard, python=args.python, label=str(index), timeout_seconds=max(12, args.timeout_seconds))
        if passed < 0:
            return 1
        passed_total += passed
        selected_files += len(shard)
    print(f"\nSUCCESS: {passed_total} tests passed across {selected_files} files in isolated groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
