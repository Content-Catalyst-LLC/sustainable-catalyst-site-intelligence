from pathlib import Path
import json
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
required = {
    "backend/app/version.py": ['APP_VERSION = "2.4.0"', 'RELEASE_NAME = "Scientific and Earth Systems Observatory"'],
    "backend/app/scientific_earth_systems_observatory.py": ["build_science_overview", "build_science_stac", "build_science_series_points", "fabrication_fallback"],
    "backend/app/main.py": ["/public/scientific-earth-systems", "/public/scientific-earth-systems/stac", "/public/scientific-earth-systems/timeseries"],
    "backend/public_app/index.html": ['data-route="science"', 'id="scienceStudio"', "science-v240.js", "science-v240.css"],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.4.0"', 'route==="science"', "SCScienceV240"],
    "backend/public_app/assets/science-v240.js": ["SCScienceV240", "/public/scientific-earth-systems/records", "downloadCsv"],
    "backend/public_app/assets/science-v240.css": [".science-studio", ".science-records"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.4.0", "sc_scientific_earth_systems_observatory"],
    "docs/RELEASE_MANIFEST_V240.json": ['"release": "2.4.0"', '"paid_provider_required": false', '"fabricated_fallback": false'],
    "CHANGELOG.md": ["2.4.0", "Scientific and Earth Systems Observatory"],
    "README.md": ["Current release:** v2.4.0", "/app/?view=science"],
}
missing = []
for relative, markers in required.items():
    path = root / relative
    if not path.is_file():
        missing.append(f"missing file: {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            missing.append(f"missing marker in {relative}: {marker}")
manifest = json.loads((root / "docs/RELEASE_MANIFEST_V240.json").read_text())
if manifest.get("paid_provider_required") is not False:
    missing.append("release manifest must prohibit a paid API requirement")
if manifest.get("fabricated_fallback") is not False:
    missing.append("release manifest must prohibit fabricated scientific fallback records")
if missing:
    raise SystemExit("\n".join(missing))
print("Site Intelligence v2.4.0 release contract passed.")
