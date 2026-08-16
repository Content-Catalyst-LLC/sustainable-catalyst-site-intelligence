#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/validate_v4360_release_contract.py")], check=True)
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php").read_text(encoding="utf-8")
index = (ROOT / "backend/public_app/index.html").read_text(encoding="utf-8")
app = (ROOT / "backend/public_app/assets/app.js").read_text(encoding="utf-8")
science = (ROOT / "backend/public_app/assets/science-v240.js").read_text(encoding="utf-8")
main = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
sw = (ROOT / "backend/public_app/service-worker.js").read_text(encoding="utf-8")
assert "Version: 4.37.0" in wp and "site-intelligence-v4.37.0" in wp
assert 'data-scsi-release="4.37.0"' in index
assert 'const APP_VERSION="4.37.0"' in app
assert 'data-ocean-entry="hub"' in index
assert 'id="oceanObservationStudio"' in index
assert "ocean-observation-v4360.js" in sw and "ocean-observation-v4360.css" in sw
assert 'id="scienceWorkspaceSelect"' in index
assert all(f'<option value="{domain}">{title}</option>' in index for domain, title in (("earth", "Earth"), ("ocean", "Ocean"), ("space", "Space")))
assert "/public/scientific-earth-systems/discovery" in main
assert "SCSIOceanObservationV4360" in science and "SCSISolarSystemV4400" in science
for file in (
    "backend/app/ocean_observation_marine_systems_v4360.py",
    "backend/tests/test_global_ocean_intelligence_ii_v4360.py",
    "backend/public_app/assets/ocean-observation-v4360.css",
    "backend/public_app/assets/ocean-observation-v4360.js",
    "scripts/validate_v4360_release_contract.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4360.md",
    "SITE_INTELLIGENCE_V4360_OCEAN_OBSERVATION_AUDIT.md",
    "SITE_INTELLIGENCE_V4360_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4360_R2_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4360_R3_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4360_R3_TERMINAL_COMMANDS.txt",
    "SITE_INTELLIGENCE_V4360_R4_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4360_R4_TERMINAL_COMMANDS.txt",
    "SITE_INTELLIGENCE_V4360_R4_BUILD_VALIDATION.txt",
    "SITE_INTELLIGENCE_V4360_R2_TERMINAL_COMMANDS.txt",
    "backend/tests/test_science_core_decoupling_v4360_r2.py",
    "backend/tests/test_science_ocean_hydration_v4360_r3.py",
    "scripts/browser_science_core_decoupling_v4360_r2.py",
    "scripts/browser_science_ocean_hydration_v4360_r3.py",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4360_R2.md",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4360_R3.md",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4360_R4.md",
    "SITE_INTELLIGENCE_V4360_R2_SCIENCE_DISCOVERY_AUDIT.md",
    "SITE_INTELLIGENCE_V4360_R3_HYDRATION_AUDIT.md",
    "SITE_INTELLIGENCE_V4360_R4_CONTROLLER_ROUTE_PROMINENCE_AUDIT.md",
    "backend/tests/test_science_ocean_workspace_controller_r4.py",
    "scripts/browser_science_ocean_workspace_controller_v4360_r4.py",
):
    assert (ROOT / file).is_file(), file
assert 'data-ocean-hydration-state="idle"' in index
assert 'oceanHydrationState="ready"' in (ROOT / "backend/public_app/assets/ocean-observation-v4360.js").read_text(encoding="utf-8")
assert 'v4.37.0' in (ROOT / "backend/app/scientific_earth_systems_observatory.py").read_text(encoding="utf-8")
assert '/app/assets/science-v240.js?v=4.37.0' in index
assert '/app/assets/ocean-observation-v4360.js?v=4.37.0' in index
assert '/app/assets/app.js?v=4.37.0' in index
assert '/app/assets/unified-platform-v4000.css?v=4.37.0' in index
assert 'data-space-entry="hub" data-nav-group="places-systems"' in index
assert 'Explore Ocean' in index and 'Explore Space' in index
assert 'const REPAIR="r4"' in sw
print("PASS: v4.37.0 R4 static release validation")
