from pathlib import Path
import json
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
required = {
    "backend/app/version.py": ['APP_VERSION = "2.2.0"', 'RELEASE_NAME = "Economics, Markets, and Sustainability Signals"'],
    "backend/app/economics_markets_sustainability.py": ["build_economics_overview", "OFFICIAL RELEASE", "licensed_real_time_exchange_data"],
    "backend/app/main.py": ["/public/economics-sustainability", "build_economic_comparison"],
    "backend/public_app/index.html": ['data-route="economics"', 'id="economicsStudio"', "economics-v220.js", "economics-v220.css"],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.2.0"', 'route==="economics"', "SCEconomicsV220"],
    "backend/public_app/assets/economics-v220.js": ["SCEconomicsV220", "/public/economics-sustainability/records", "downloadCsv"],
    "backend/public_app/assets/economics-v220.css": [".economics-studio", ".economics-records"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.2.0", "sc_economics_sustainability_observatory"],
    "docs/RELEASE_MANIFEST_V220.json": ['"release": "2.2.0"', '"free_provider_only": true'],
    "CHANGELOG.md": ["2.2.0", "Economics, Markets, and Sustainability Signals"],
    "README.md": ["Current release:** v2.2.0", "/app/?view=economics"],
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
manifest = json.loads((root / "docs/RELEASE_MANIFEST_V220.json").read_text())
if manifest.get("paid_api_required") is not False:
    missing.append("release manifest must prohibit a paid API requirement")
if manifest.get("licensed_real_time_exchange_feed_claimed") is not False:
    missing.append("release manifest must not claim licensed real-time exchange data")
if missing:
    raise SystemExit("\n".join(missing))
print("Site Intelligence v2.2.0 release contract passed.")
