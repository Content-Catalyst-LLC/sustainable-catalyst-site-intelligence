from pathlib import Path
import json
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
required = {
    "backend/app/version.py": ['APP_VERSION = "2.3.0"', 'RELEASE_NAME = "International Law and Global Governance Observatory"'],
    "backend/app/international_law_observatory.py": ["build_law_overview", "build_country_legal_profile", "binding_effect"],
    "backend/app/main.py": ["/public/international-law-observatory", "build_authority_matrix"],
    "backend/public_app/index.html": ['data-route="law"', 'id="lawStudio"', "law-v230.js", "law-v230.css"],
    "backend/public_app/assets/app.js": ['const APP_VERSION="2.3.0"', 'route==="law"', "SCLawV230"],
    "backend/public_app/assets/law-v230.js": ["SCLawV230", "/public/international-law-observatory/records", "downloadCsv"],
    "backend/public_app/assets/law-v230.css": [".law-studio", ".law-records"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.3.0", "sc_international_law_governance_observatory"],
    "docs/RELEASE_MANIFEST_V230.json": ['"release": "2.3.0"', '"paid_api_required": false', '"binding_effect_inferred_automatically": false'],
    "CHANGELOG.md": ["2.3.0", "International Law and Global Governance Observatory"],
    "README.md": ["Current release:** v2.3.0", "/app/?view=law"],
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
manifest = json.loads((root / "docs/RELEASE_MANIFEST_V230.json").read_text())
if manifest.get("paid_api_required") is not False:
    missing.append("release manifest must prohibit a paid API requirement")
if manifest.get("binding_effect_inferred_automatically") is not False:
    missing.append("release manifest must prohibit automatic binding-effect inference")
if manifest.get("legal_advice_provided") is not False:
    missing.append("release manifest must prohibit legal advice")
if missing:
    raise SystemExit("\n".join(missing))
print("Site Intelligence v2.3.0 release contract passed.")
