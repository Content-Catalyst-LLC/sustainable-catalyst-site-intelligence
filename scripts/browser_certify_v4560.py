#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.56.0"


def main() -> None:
    config=(ROOT/"web/config.js").read_text(encoding="utf-8")
    assert 'release: "4.56.0"' in config
    assert 'runtimeMode: "standalone-production-certified"' in config
    prior=ROOT/"scripts/browser_certify_v455322.py"
    assert prior.is_file(), prior
    subprocess.run([sys.executable, str(prior)], cwd=ROOT, check=True)
    print("V4560_BROWSER_CERTIFICATION=PASS")

if __name__=="__main__": main()
