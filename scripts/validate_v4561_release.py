#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.56.1"
NAME = "Platform Core International Law Bridge & Connector Activation"

required = [
    "backend/app/version.py",
    "backend/app/core_domain_bridge_v4561.py",
    "backend/app/routers/core_domain_bridge.py",
    "backend/data/core_domain_bridge_registry_v4561.json",
    "backend/tests/test_v4561_platform_core_domain_bridge_activation.py",
    "deploy/contabo/upgrade_site_intelligence_backend_v4_56_1_contabo.sh",
    "deploy/contabo/upgrade_site_intelligence_web_v4_56_1_contabo.sh",
    "docs/V4561_RELEASE_NOTES.md",
]
for rel in required:
    path = ROOT / rel
    assert path.exists(), f"missing: {rel}"
    print(f"PASS: file exists: {rel}")

for rel in [
    "backend/app/core_domain_bridge_v4561.py",
    "backend/app/routers/core_domain_bridge.py",
    "backend/tests/test_v4561_platform_core_domain_bridge_activation.py",
]:
    py_compile.compile(str(ROOT / rel), doraise=True)
    print(f"PASS: Python compile: {rel}")

version = (ROOT / "backend/app/version.py").read_text(encoding="utf-8")
assert f'APP_VERSION = "{VERSION}"' in version
assert f'RELEASE_NAME = "{NAME}"' in version
print("PASS: release identity")

registry = json.loads((ROOT / "backend/data/core_domain_bridge_registry_v4561.json").read_text(encoding="utf-8"))
assert registry["version"] == VERSION
assert registry["catalog_targets"]["minimum_sources"] == 40
assert registry["catalog_targets"]["minimum_connectors"] == 39
assert set(registry["workspace_coverage"]) == {"law", "economics", "humanitarian", "science", "resources", "dossiers"}
print("PASS: cross-domain source coverage registry")

route_registry = (ROOT / "backend/app/route_registry_v4430.py").read_text(encoding="utf-8")
assert '"registry_version": "2.8.0"' in route_registry
assert 'CapabilitySpec("core-domain-bridge"' in route_registry
print("PASS: capability registry 2.8.0")

global_bridge = (ROOT / "backend/app/global_conditions_observatory.py").read_text(encoding="utf-8")
assert "internal_service" in global_bridge
assert 'effective_path = "/v1/" + effective_path[len("/api/v1/"):]' in global_bridge
assert 'X-SC-Public-Key' in global_bridge
print("PASS: private/public Core read routing")

web = (ROOT / "web/config.js").read_text(encoding="utf-8")
assert 'release: "4.56.1"' in web
assert 'runtimeMode: "standalone-production-certified-core-bridge"' in web
print("PASS: standalone web release identity")

plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
assert "Version: 4.56.1" in plugin
assert "const VERSION = '4.56.1';" in plugin
assert "const WORDPRESS_ROLE = 'public-site-launch-bridge';" in plugin
print("PASS: WordPress bridge identity/non-authority")

policies = []
for path in (ROOT / "backend/data").glob("*.json"):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    if payload.get("version") == VERSION:
        policies.append(path.name)
assert "core_domain_bridge_registry_v4561.json" in policies
assert len(policies) >= 47, len(policies)
print(f"PASS: {len(policies)} release-bound/current policies aligned to {VERSION}")

print("V4561_RELEASE_VALIDATION=PASS")
