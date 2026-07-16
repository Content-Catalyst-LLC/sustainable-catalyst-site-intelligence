from pathlib import Path
import json
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]).resolve()
required={
 "backend/app/version.py":['APP_VERSION = "2.9.0"','RELEASE_NAME = "Comparative Intelligence and Scenario Studio"'],
 "backend/app/comparative_scenario_studio_v290.py":["build_comparison_matrix","build_transparent_scenario","build_correlation_review","build_comparison_packet","silent_normalization"],
 "backend/app/main.py":["/public/comparative-scenario-studio/compare","/public/comparative-scenario-studio/scenario","/public/comparative-scenario-studio/packet"],
 "backend/public_app/index.html":['data-route="scenarios"','id="scenarioStudio"','scenarios-v290.js','No forecast or ranking'],
 "backend/public_app/assets/app.js":['const APP_VERSION="2.9.0"','route==="scenarios"','SCScenariosV290'],
 "backend/public_app/assets/scenarios-v290.js":["SCScenariosV290","/public/comparative-scenario-studio/compare","/public/comparative-scenario-studio/scenario"],
 "backend/public_app/assets/scenarios-v290.css":[".scenario-studio",".scenario-matrix"],
 "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.9.0","sc_comparative_intelligence_scenario_studio"],
 "docs/RELEASE_MANIFEST_V290.json":['"version": "2.9.0"','"paid_api_required": false','"silent_normalization": false','"forecasting": false'],
 "backend/tests/test_comparative_scenario_studio_v290.py":["test_comparison_matrix_preserves_compatibility","test_public_routes_and_interface"],
 "CHANGELOG.md":["2.9.0","Comparative Intelligence and Scenario Studio"],
 "README.md":["Current release:** v2.9.0","/app/?view=scenarios"],
}
missing=[]
for relative,markers in required.items():
 path=root/relative
 if not path.is_file():missing.append(f"missing file: {relative}");continue
 text=path.read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text:missing.append(f"missing marker in {relative}: {marker}")
manifest=json.loads((root/'docs/RELEASE_MANIFEST_V290.json').read_text(encoding='utf-8'))
for key in ('paid_api_required','fabricated_fallback','silent_normalization','ranking_created','forecasting','causal_inference'):
 if manifest.get(key) is not False:missing.append(f"release manifest must set {key}=false")
if missing:raise SystemExit('\n'.join(missing))
print('Site Intelligence v2.9.0 release contract passed.')
