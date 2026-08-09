#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PYTHON=os.environ.get('PYTHON') or sys.executable
os.chdir(ROOT)
os.environ.setdefault('PYTEST_DISABLE_PLUGIN_AUTOLOAD','1')
os.environ.setdefault('PYTHONPATH',str(ROOT/'backend'))
import subprocess
proc=subprocess.run([PYTHON,'-m','pytest','-q','backend/tests'],env=os.environ.copy())
raise SystemExit(proc.returncode)
