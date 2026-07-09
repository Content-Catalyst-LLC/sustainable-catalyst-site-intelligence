#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8091 --reload
