#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
requirements = {
    "backend/app/version.py": ['APP_VERSION = "4.17.0"'],
    "backend/app/main.py": ["is_app_surface", "frame-ancestors", "public_embeds_enabled"],
    "backend/public_app/index.html": ["map-fallback-v3221.js", 'id="spatialEvidenceMap"', 'src="/app/assets/app.js" defer'],
    "backend/public_app/assets/map-fallback-v3221.js": ["SCSIMapReliability", "static-fallback", "carto-unavailable"],
    "backend/public_app/assets/map-fallback-v3221.css": ["scsi-static-map", "scsi-map-tile-fallback"],
    "backend/public_app/assets/spatial-v2150.js": ['const VERSION = "4.17.0"', "L.geoJSON", "renderEvidence"],
    "backend/public_app/service-worker.js": ['const RELEASE="4.17.0"', "map-fallback-v3221.js", "map-fallback-v3221.css"],
    "backend/public_app/manifest.webmanifest": ["release=4.17.0"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 4.17.0", "mapFallbackUrl"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["loadLocalMapFallback", "setTimeout(useFallback,3500)"],
    "backend/tests/test_map_runtime_repair_v3221.py": ["test_embeddable_app_uses_csp_without_conflicting_frame_header", "test_spatial_evidence_has_a_real_map_surface"],
    "RELEASE_NOTES_SITE_INTELLIGENCE_V3221.md": ["847 inherited and new regression tests passed", "Browser automation could not be used"],
}
for relative, needles in requirements.items():
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"Missing required release file: {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing {needle!r} in {relative}")
manifest_path = ROOT / "MANIFEST.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release") != "4.17.0":
        raise SystemExit("MANIFEST.json is not aligned to v4.17.0")
print("Site Intelligence v4.17.0 map runtime repair contract passed.")
