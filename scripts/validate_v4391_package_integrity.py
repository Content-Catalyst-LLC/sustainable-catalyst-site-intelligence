#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "sustainable-catalyst-site-intelligence/"
TRACKED = [
    "assets/sc-site-intelligence.js",
    "assets/sc-site-intelligence.css",
    "sustainable-catalyst-site-intelligence.php",
]

parser = argparse.ArgumentParser()
parser.add_argument("--wordpress-zip", required=True)
args = parser.parse_args()
wp_zip = Path(args.wordpress_zip)
if not wp_zip.is_file():
    raise SystemExit(f"FAIL: WordPress ZIP not found: {wp_zip}")

with ZipFile(wp_zip) as zf:
    source_root = ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence"
    source_files = sorted(path for path in source_root.rglob("*") if path.is_file())
    expected_names = {PREFIX + path.relative_to(source_root).as_posix() for path in source_files}
    archive_names = {name for name in zf.namelist() if not name.endswith("/")}
    missing = sorted(expected_names - archive_names)
    unexpected = sorted(archive_names - expected_names)
    if missing:
        raise SystemExit("FAIL: WordPress ZIP missing source files: " + ", ".join(missing[:10]))
    if unexpected:
        raise SystemExit("FAIL: WordPress ZIP contains unexpected files: " + ", ".join(unexpected[:10]))
    for source in source_files:
        relative = source.relative_to(source_root).as_posix()
        archive_name = PREFIX + relative
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        zip_hash = hashlib.sha256(zf.read(archive_name)).hexdigest()
        if source_hash != zip_hash:
            raise SystemExit(f"FAIL: repository/WordPress ZIP asset mismatch: {relative}")
    plugin_text = zf.read(PREFIX + "sustainable-catalyst-site-intelligence.php").decode("utf-8")
    if "Version: 4.39.1" not in plugin_text or "site-intelligence-v4.39.1" not in plugin_text:
        raise SystemExit("FAIL: WordPress ZIP release identity is not v4.39.1")
print(f"PASS: repository and packaged WordPress v4.39.1 files are byte-identical ({len(source_files)} files)")
