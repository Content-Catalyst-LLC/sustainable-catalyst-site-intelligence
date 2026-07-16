#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "backend/app/version.py": ["2.24.0", "Open Standards, Federation, and Institutional Data Exchange"],
    "backend/app/config.py": ["federation_exchange_enabled", "federation_records_path", "federation_signing_key"],
    "backend/app/federation_exchange_v2240.py": ["class InstitutionalDataExchange", "def register_record(", "def build_manifest(", "def validate_manifest(", "def import_preview(", "def accept_import("],
    "backend/app/main.py": ["/public/institutional-data-exchange", "/public/institutional-data-exchange/catalog", "/admin/institutional-data-exchange/control-center", "/admin/institutional-data-exchange/import-preview"],
    "backend/data/federation_policy_v2240.json": ["automatic_remote_fetch", "signature_proves_identity", "trust_policy_required"],
    "backend/data/federation_context_v2240.json": ["http://www.w3.org/ns/dcat#", "http://www.w3.org/ns/prov#"],
    "backend/public_app/index.html": ["data-route=\"federation\"", "id=\"institutionalDataExchangeStudio\"", "/app/assets/federation-v2240.js?v=2.24.0"],
    "backend/public_app/assets/app.js": ["SCInstitutionalFederationV2240", "route===\"federation\""],
    "backend/public_app/service-worker.js": ["const RELEASE=\"2.24.0\"", "/app/assets/federation-v2240.js"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.24.0", "sc_public_institutional_data_exchange", "sc_institutional_data_exchange_control_center"],
    "docs/RELEASE_MANIFEST_V2240.json": ["dcat_compatible_jsonld", "signed_manifests", "preview_first_imports"],
    "README.md": ["Current release:** v2.24.0 — Open Standards, Federation, and Institutional Data Exchange", "/app/?view=federation"],
    "CHANGELOG.md": ["## 2.24.0 — Open Standards, Federation, and Institutional Data Exchange"]
}
errors = []
for rel, markers in CHECKS.items():
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        continue
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel}: missing {marker}")
manifest = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2240.json").read_text())
for key in ["dcat_compatible_jsonld", "prov_compatible_provenance", "geojson_exchange", "csv_exchange", "machine_readable_licenses", "signed_manifests", "sha256_integrity", "trust_policies", "preview_first_imports", "human_import_confirmation", "quarantine_receipts", "hosting_mode_distinction"]:
    if manifest.get(key) is not True:
        errors.append(f"release manifest {key} must be true")
for key in ["automatic_remote_fetch", "automatic_import", "automatic_remote_write", "signature_proves_identity", "public_private_records_exposed", "individual_tracking", "social_scoring", "autonomous_consequential_actions"]:
    if manifest.get(key) is not False:
        errors.append(f"release manifest {key} must be false")
for rel in manifest.get("writable_state_excluded", []):
    if (ROOT / rel).exists():
        errors.append(f"writable runtime directory packaged: {rel}")
if errors:
    print("Site Intelligence v2.24.0 release contract failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)
print("Site Intelligence v2.24.0 release contract passed.")
