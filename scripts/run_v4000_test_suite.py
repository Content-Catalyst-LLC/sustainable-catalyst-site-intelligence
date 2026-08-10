#!/usr/bin/env python3
"""Run the complete v4.17.0 pytest inventory once with bounded teardown.

The suite output is file-backed so inherited connector executor threads cannot hold the
installer's stdout pipe open after pytest has already emitted a complete pass summary.
"""
from __future__ import annotations
import os, sys, tempfile
from pathlib import Path
from run_v3310_test_groups import completed_pass, passed_count, run_file_backed

ROOT=Path(__file__).resolve().parents[1]
PYTHON=os.environ.get('PYTHON') or sys.executable
MIN_EXPECTED_TESTS=1084

def main()->int:
    base=Path(os.environ.get('SC_SI_RUNTIME_STATE_ROOT') or tempfile.mkdtemp(prefix='scsi-v4000-tests-'))
    base.mkdir(parents=True,exist_ok=True)
    output_path=base/'pytest-complete.txt'
    rc,output,interrupted=run_file_backed([PYTHON,'-m','pytest','-q','--disable-warnings','backend/tests'],base/'suite-runtime',120,output_path)
    print(output,end='',flush=True)
    actual=passed_count(output)
    if not completed_pass(output) or actual < MIN_EXPECTED_TESTS:
        raise SystemExit(f'ERROR: complete test suite reported {actual} passes; expected at least {MIN_EXPECTED_TESTS}.')
    if rc and not interrupted: raise SystemExit(f'ERROR: pytest exited with status {rc}.')
    if interrupted: print('PASS: complete pytest summary was recorded; lingering teardown was terminated.',flush=True)
    print(f'PASS: all {actual} collected tests passed in the complete file-backed suite.',flush=True)
    return 0
if __name__=='__main__': raise SystemExit(main())
