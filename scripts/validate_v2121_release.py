from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
checks = {
    "backend/app/version.py": ['APP_VERSION = "2.12.1"', 'RELEASE_NAME = "Production Offline, Mobile, and Embed Reliability Patch"'],
    "backend/app/offline_mobile_accessibility_performance_v2120.py": ["build_reliability", "partial_install_recovery", "source_window_checked"],
    "backend/public_app/index.html": ['data-route="experience"', 'id="offlineExperienceStudio"', 'v2.12.1'],
    "backend/public_app/assets/app.js": ['APP_VERSION="2.12.1"', 'updateViaCache:"none"', "SC_SI_ACTIVATE_UPDATE", "version:APP_VERSION"],
    "backend/public_app/service-worker.js": ['const RELEASE="2.12.1"', "Promise.allSettled", "trimCache", "MAX_DATA_AGE_MS", "SC_SI_CLEAR_OFFLINE"],
    "backend/public_app/manifest.webmanifest": ["release=2.12.1", '"display_override"', '"shortcuts"'],
    "backend/public_app/offline.html": ["RELEASE 2.12.1", "Reset offline cache", "key.startsWith('scsi-')"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php": ["Version: 2.12.1", "data-scsi-embed-frame", "Open Site Intelligence in a new tab"],
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js": ["setupResponsiveEmbeds", "event.origin !== record.origin", "event.source !== record.frame.contentWindow"],
    "docs/RELEASE_MANIFEST_V2121.json": ['"version": "2.12.1"', '"bounded": true', '"source_window_checked": true', '"paid_api_required": false'],
    "README.md": ["Current release:** v2.12.1", "/public/offline-experience/reliability"],
    "CHANGELOG.md": ["## 2.12.1 — Production Offline, Mobile, and Embed Reliability Patch"],
}
for relative, needles in checks.items():
    path = root / relative
    if not path.exists():
        raise SystemExit(f"Missing {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Missing contract marker {needle!r} in {relative}")
manifest = json.loads((root / "backend/public_app/manifest.webmanifest").read_text(encoding="utf-8"))
if manifest.get("scope") != "/app/" or len(manifest.get("icons", [])) < 2 or len(manifest.get("shortcuts", [])) < 3:
    raise SystemExit("PWA manifest is incomplete.")
release = json.loads((root / "docs/RELEASE_MANIFEST_V2121.json").read_text(encoding="utf-8"))
if release.get("paid_api_required") is not False or release.get("server_user_tracking") is not False:
    raise SystemExit("Public-first governance boundary is missing.")
print("Site Intelligence v2.12.1 release contract passed.")
