from pathlib import Path
import json
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]).resolve()
required={
 "backend/app/version.py":['APP_VERSION = "2.7.0"','RELEASE_NAME = "Unified Country and Regional Intelligence Dossiers"'],
 "backend/app/unified_country_regional_dossiers.py":["build_country_dossier","build_regional_dossier","build_dossier_comparison","composite_score_created"],
 "backend/app/main.py":["/public/intelligence-dossiers/country","/public/intelligence-dossiers/region","/public/intelligence-dossiers/diagnostics"],
 "backend/public_app/index.html":['data-route="dossiers"','id="dossierStudio"','dossiers-v270.js','No composite score or country ranking'],
 "backend/public_app/assets/app.js":['const APP_VERSION="2.7.0"','route==="dossiers"','SCDossiersV270'],
 "backend/public_app/assets/dossiers-v270.js":["SCDossiersV270","/public/intelligence-dossiers/country","no composite score"],
 "backend/public_app/assets/dossiers-v270.css":[".dossier-studio",".dossier-coverage"],
 "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php":["Version: 2.7.0","sc_country_regional_intelligence_dossiers"],
 "docs/RELEASE_MANIFEST_V270.json":['"version": "2.7.0"','"paid_api_required": false','"composite_score": false'],
 "backend/tests/test_unified_country_regional_dossiers_v270.py":["test_country_dossier_preserves_domains_without_score","test_public_routes"],
 "CHANGELOG.md":["2.7.0","Unified Country and Regional Intelligence Dossiers"],
 "README.md":["Current release:** v2.7.0","/app/?view=dossiers"],
}
missing=[]
for relative,markers in required.items():
 path=root/relative
 if not path.is_file():missing.append(f"missing file: {relative}");continue
 text=path.read_text(encoding="utf-8")
 for marker in markers:
  if marker not in text:missing.append(f"missing marker in {relative}: {marker}")
manifest=json.loads((root/'docs/RELEASE_MANIFEST_V270.json').read_text(encoding='utf-8'))
for key in ('paid_api_required','fabricated_fallback','composite_score','country_ranking','causal_inference','legal_determination','humanitarian_priority','national_security_rating'):
 if manifest.get(key) is not False:missing.append(f"release manifest must set {key}=false")
if missing:raise SystemExit('\n'.join(missing))
print('Site Intelligence v2.7.0 release contract passed.')
