#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "venv", ".venv", ".runtime"}
EXCLUDED_FILES = {"MANIFEST.json", ".DS_Store"}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    return relative.as_posix() not in EXCLUDED_FILES and path.suffix not in {".pyc", ".pyo"}

files = []
for path in sorted((p for p in ROOT.rglob("*") if p.is_file() and included(p)), key=lambda p: p.relative_to(ROOT).as_posix()):
    data = path.read_bytes()
    files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"release": "4.39.1", "file_count": len(files), "files": files}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(files)}-file immutable v4.39.1 release manifest.")
