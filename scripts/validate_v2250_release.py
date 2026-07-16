from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
checks = {
    "backend/app/version.py": ["2.25.0", "Security, Privacy, Governance, and Production Scale"],
    "backend/app/production_governance_v2250.py": ["class ProductionGovernanceCenter", "def apply_migrations", "def create_api_key", "def create_backup", "def enqueue_job"],
    "backend/app/main.py": ["/public/production-governance", "/admin/production-governance/control-center"],
    "backend/public_app/index.html": ['data-route="governance"', 'id="productionGovernanceStudio"'],
    "backend/public_app/service-worker.js": ["governance-v2250.js", "governance-v2250.css"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.25.0", "sc_public_production_governance", "sc_production_governance_control_center"],
    "README.md": ["Current release:** v2.25.0 — Security, Privacy, Governance, and Production Scale"],
}
for relative, markers in checks.items():
    text = (ROOT / relative).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"{relative}: missing {marker}")
policy = json.loads((ROOT / "docs/RELEASE_MANIFEST_V2250.json").read_text())
required_true = ["sqlite_migrations", "scoped_api_keys", "api_key_hash_storage", "hash_chained_audit", "privacy_request_tracking", "preview_first_retention", "digest_verified_backups", "persistent_job_queue", "deployment_receipts"]
for key in required_true:
    if policy.get(key) is not True:
        raise SystemExit(f"Release policy requires {key}=true")
required_false = ["automatic_privacy_deletion", "automatic_restore", "automatic_queue_worker", "distributed_rate_limiter", "automatic_compliance_claim", "secrets_publicly_exposed"]
for key in required_false:
    if policy.get(key) is not False:
        raise SystemExit(f"Release policy requires {key}=false")
if (ROOT / "backend/data/production_governance_v2250").exists():
    raise SystemExit("Writable production-governance state is present in the source release.")
print("Site Intelligence v2.25.0 release contract passed.")
