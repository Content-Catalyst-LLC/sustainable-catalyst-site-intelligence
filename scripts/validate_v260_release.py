from pathlib import Path
import json
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]).resolve()
required={
 "backend/app/version.py":['APP_VERSION = "2.6.0"','RELEASE_NAME = "Trade, Energy, and Resource Security Observatory"'],
 "backend/app/trade_energy_resource_security_observatory.py":["build_overview","build_records","build_dependencies","build_country_profile","risk_score_created"],
 "backend/app/main.py":["/public/trade-energy-resources","/public/trade-energy-resources/dependencies","/public/trade-energy-resources/diagnostics"],
 "backend/public_app/index.html":['data-route="resources"','id="resourceStudio"','resources-v260.js','No proprietary security score'],
 "backend/public_app/assets/app.js":['const APP_VERSION="2.6.0"','route==="resources"','SCResourcesV260'],
 "backend/public_app/assets/resources-v260.js":["SCResourcesV260","/public/trade-energy-resources/records","no proprietary risk score"],
 "backend/public_app/assets/resources-v260.css":[".resource-studio",".resource-records"],
 "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.6.0","sc_trade_energy_resource_security_observatory"],
 "docs/RELEASE_MANIFEST_V260.json":['"version": "2.6.0"','"paid_api_required": false','"proprietary_risk_score": false'],
 "backend/tests/test_trade_energy_resource_security_observatory_v260.py":["test_sanitizes_and_classifies","test_public_routes"],
 "CHANGELOG.md":["2.6.0","Trade, Energy, and Resource Security Observatory"],
 "README.md":["Current release:** v2.6.0","/app/?view=resources"],
}
missing=[]
for relative,markers in required.items():
 path=root/relative
 if not path.is_file():missing.append(f"missing file: {relative}");continue
 text=path.read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text:missing.append(f"missing marker in {relative}: {marker}")
manifest=json.loads((root/'docs/RELEASE_MANIFEST_V260.json').read_text(encoding='utf-8'))
for key in ('paid_api_required','proprietary_risk_score','sanctions_screening','investment_advice','national_security_determination','fabricated_fallback'):
 if manifest.get(key) is not False:missing.append(f"release manifest must set {key}=false")
if missing:raise SystemExit('\n'.join(missing))
print('Site Intelligence v2.6.0 release contract passed.')
