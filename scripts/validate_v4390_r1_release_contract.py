#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


plugin = text("wordpress-plugin/sustainable-catalyst-site-intelligence/sustainable-catalyst-site-intelligence.php")
stylesheet = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.css")
javascript = text("wordpress-plugin/sustainable-catalyst-site-intelligence/assets/sc-site-intelligence.js")
readme = text("README.md")

require("Version: 4.39.0" in plugin, "R1 must preserve the WordPress 4.39.0 release-gate identity")
require("APP_VERSION = \"4.39.0\"" in text("backend/app/version.py"), "R1 must preserve backend 4.39.0")
for token in (
    "$home_images",
    "earth-blue-marble.webp",
    "space-webb-deep-field.webp",
    "ocean-noaa-seafloor.webp",
    "scsi-home-summary__visual-media",
    "scsi-home-summary__image-credit",
    "$this->live_intelligence_shortcode([",
    "scsi-home-summary__ticker",
):
    require(token in plugin, f"homepage visual/ticker contract missing {token}")
require("has_shortcode((string) $post->post_content, 'sc_site_intelligence_home')" in plugin, "integrated ticker duplicate protection missing")
require("data-home-scroll" not in plugin and "scsi-home-summary__signal-layer" not in plugin, "abandoned carousel controls remain in the homepage shortcode")
for token in (
    ".scsi-home-summary__visual-media",
    ".scsi-home-summary__visual-frame--earth",
    ".scsi-home-summary__visual-frame--space",
    ".scsi-home-summary__visual-frame--ocean",
    ".scsi-home-summary__ticker",
    "@keyframes scsi-home-signal-pulse",
    "prefers-reduced-motion",
    "forced-colors",
):
    require(token in stylesheet, f"homepage visual stylesheet missing {token}")
require("setupLiveIntelligence" in javascript and "is-paused" in javascript, "inherited ticker controller contract missing")

image_paths = [
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/images/site-intelligence-home/earth-blue-marble.webp",
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/images/site-intelligence-home/space-webb-deep-field.webp",
    "wordpress-plugin/sustainable-catalyst-site-intelligence/assets/images/site-intelligence-home/ocean-noaa-seafloor.webp",
]
for relative in image_paths:
    path = ROOT / relative
    require(path.is_file(), f"missing optimized homepage image {relative}")
    if path.is_file():
        payload = path.read_bytes()
        require(len(payload) >= 50_000, f"homepage image is unexpectedly small: {relative}")
        require(len(payload) <= 350_000, f"homepage image exceeds the bounded web payload: {relative}")
        require(payload[:4] == b"RIFF" and payload[8:12] == b"WEBP", f"homepage image is not WebP: {relative}")

for relative in (
    "source-materials/site-intelligence-home/earth-blue-marble-source.jpg",
    "source-materials/site-intelligence-home/space-webb-deep-field-source.png",
    "source-materials/site-intelligence-home/ocean-noaa-seafloor-source.jpg",
    "RELEASE_NOTES_SITE_INTELLIGENCE_V4390_R1.md",
    "SITE_INTELLIGENCE_V4390_R1_IMAGE_CREDITS.md",
    "SITE_INTELLIGENCE_V4390_R1_VISUAL_AUDIT.md",
    "SITE_INTELLIGENCE_V4390_R1_INSTALL_AND_TEST.md",
    "SITE_INTELLIGENCE_V4390_R1_BUILD_VALIDATION.txt",
    "SITE_INTELLIGENCE_V4390_R1_TERMINAL_COMMANDS.txt",
):
    require((ROOT / relative).is_file(), f"missing R1 release file {relative}")

require("v4.39.0 R1" in readme and "Integrated Live Ticker" in readme, "README R1 release documentation missing")

if errors:
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    raise SystemExit(1)
print("PASS: v4.39.0 R1 visual console, imagery, ticker, accessibility, and release-gate contract")
