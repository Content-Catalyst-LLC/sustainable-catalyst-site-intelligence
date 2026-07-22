from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_v2250_release_contract_markers():
    checks = {
        "backend/app/version.py": ["3.19.0", "Connected Public Intelligence and Evidence Platform"],
        "backend/app/production_governance_v2250.py": ["class ProductionGovernanceCenter", "def apply_migrations", "def create_api_key", "def create_backup", "def enqueue_job"],
        "backend/public_app/index.html": ["data-route=\"governance\"", "id=\"productionGovernanceStudio\""],
        "backend/public_app/service-worker.js": ["/app/assets/governance-v2250.js", "/app/assets/governance-v2250.css"],
        "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 3.19.0", "sc_public_production_governance", "sc_production_governance_control_center"],
        "README.md": ["Current release:** v3.19.0 — Connected Public Intelligence and Evidence Platform"],
    }
    for rel, markers in checks.items():
        text = (ROOT / rel).read_text()
        for marker in markers:
            assert marker in text, f"{rel}: {marker}"


def test_policy_manifest_refuses_unsafe_production_claims():
    data = json.loads((ROOT / "backend/data/production_governance_policy_v2250.json").read_text())
    assert data["storage"]["migration_framework"] is True
    assert data["authentication"]["keys_stored_as_hashes"] is True
    assert data["audit"]["hash_chained"] is True
    assert data["privacy"]["automatic_deletion"] is False
    assert data["backups"]["automatic_restore"] is False
    assert data["scale"]["distributed_rate_limiter"] is False
    assert data["scale"]["automatic_worker"] is False


def test_runtime_database_is_not_part_of_source_release():
    assert not (ROOT / "backend/data/production_governance_v2250").exists()
