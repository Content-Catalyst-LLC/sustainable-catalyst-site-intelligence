#!/usr/bin/env python3
"""Run pytest in a disposable process and exit without lingering executor threads."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def main() -> int:
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    sys.path.insert(0, str(BACKEND))
    import pytest

    targets = sys.argv[1:] or [str(BACKEND / "tests")]
    return int(pytest.main(["-q", "--disable-warnings", *targets]))


if __name__ == "__main__":
    status = main()
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(status)
