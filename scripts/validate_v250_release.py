from pathlib import Path
import json
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
required = {
    "backend/app/version.py": ['APP_VERSION = "2.5.0"', 'RELEASE_NAME = "Humanitarian, Conflict, and Displacement Observatory"'],
    "backend/app/humanitarian_conflict_displacement_observatory.py": ["build_overview", "build_records", "build_displacement", "build_country_profile", "fallback_used"],
    "backend/app/main.py": ["/public/humanitarian-conflict-displacement", "/public/humanitarian-conflict-displacement/timeline", "/public/humanitarian-conflict-displacement/diagnostics"],
    "backend/public_app/index.html": ['data-route="humanitarian"', 'id="humanitarianStudio"', "humanitarian-v250.js", "No fabricated crisis records"],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.5.0"', 'route==="humanitarian"', "SCHumanitarianV250"],
    "backend/public_app/assets/humanitarian-v250.js": ["SCHumanitarianV250", "/public/humanitarian-conflict-displacement/records", "no fabricated fallback"],
    "backend/public_app/assets/humanitarian-v250.css": [".humanitarian-studio", ".humanitarian-records"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.5.0", "sc_humanitarian_conflict_displacement_observatory"],
    "docs/RELEASE_MANIFEST_V250.json": ['"release": "2.5.0"', '"paid_provider_required": false', '"fabricated_fallback": false'],
    "backend/tests/test_humanitarian_conflict_displacement_observatory_v250.py": ["test_records_sanitize_and_preserve_distinctions", "test_public_routes"],
    "CHANGELOG.md": ["2.5.0", "Humanitarian, Conflict, and Displacement Observatory"],
    "README.md": ["Current release:** v2.5.0", "/app/?view=humanitarian"],
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
manifest = json.loads((root / "docs/RELEASE_MANIFEST_V250.json").read_text(encoding="utf-8"))
for key in ("paid_provider_required", "fabricated_fallback", "military_targeting", "individual_risk_scoring", "refugee_status_determination", "automated_eligibility", "emergency_warning"):
    if manifest.get(key) is not False:
        missing.append(f"release manifest must set {key}=false")
if missing:
    raise SystemExit("\n".join(missing))
print("Site Intelligence v2.5.0 release contract passed.")
