from __future__ import annotations
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1]).resolve()
required = [
    root / "backend/app/global_conditions_observatory.py",
    root / "backend/public_app/assets/global-conditions-v210.js",
    root / "backend/public_app/assets/global-conditions-v210.css",
    root / "backend/tests/test_global_conditions_observatory_v210.py",
    root / "docs/V210_GLOBAL_CONDITIONS_LIVE_MAP_OBSERVATORY.md",
]
missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
if missing:
    raise SystemExit(f"Missing v2.1.0 files: {missing}")
checks = {
    "backend/app/version.py": ['APP_VERSION = "2.1.0"', 'RELEASE_NAME = "Global Conditions and Live Map Observatory"'],
    "backend/app/main.py": ["/public/global-conditions", "build_global_conditions_features"],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.1.0"', 'route==="global"', 'SCGlobalConditionsV210'],
    "backend/public_app/index.html": ["global-conditions-v210.css", "global-conditions-v210.js", "v2.1.0"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.1.0", "sc_global_conditions_observatory", "global_conditions_observatory_shortcode"],
    "CHANGELOG.md": ["2.1.0", "Global Conditions and Live Map Observatory"],
}
for rel, markers in checks.items():
    path = root / rel
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"Missing marker {marker!r} in {rel}")
patterns = [
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"ghp_[0-9A-Za-z]{30,}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{30,}"),
    re.compile(r"sk-[0-9A-Za-z]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix.lower() in {".zip", ".png", ".jpg", ".woff", ".woff2"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for pattern in patterns:
        if pattern.search(text):
            raise SystemExit(f"Potential secret found in {path.relative_to(root)}")
for path in root.rglob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
print("Site Intelligence v2.1.0 release contract passed.")
