from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from .route_registry_v4430 import capability_manifest
from .version import APP_VERSION, RELEASE_NAME

STANDALONE_CONTRACT_VERSION = "1.0.0"
SESSION_CONTRACT_VERSION = "1.0.0"
CANONICAL_APP_PATH = "/app/"
CACHE_GENERATION = f"scsi-v{APP_VERSION}"


@dataclass(frozen=True)
class NavigationItem:
    route: str
    title: str
    description: str
    capability_id: str
    group: str
    order: int


NAVIGATION: tuple[NavigationItem, ...] = (
    NavigationItem("platform", "Connected platform", "Search and provenance", "research-evidence", "research", 10),
    NavigationItem("observatory", "Audit", "Evidence and lineage", "platform-experience", "research", 20),
    NavigationItem("launch", "Launch", "Product and portfolio", "platform-experience", "platform", 30),
    NavigationItem("overview", "Overview", "Live map and signals", "live-intelligence", "intelligence", 40),
    NavigationItem("global", "Global conditions", "Conditions and live map", "human-development", "intelligence", 50),
    NavigationItem("economics", "Economics", "Markets and sustainability", "research-evidence", "intelligence", 60),
    NavigationItem("law", "International law", "Governance and authority", "law-governance", "intelligence", 70),
    NavigationItem("science", "Science", "Earth, ocean and space", "earth-environment", "science", 80),
    NavigationItem("humanitarian", "Humanitarian", "Conflict and displacement", "human-development", "intelligence", 90),
    NavigationItem("resources", "Resources", "Trade, energy, and security", "infrastructure-energy", "intelligence", 100),
    NavigationItem("dossiers", "Dossiers", "Countries and regions", "research-evidence", "research", 110),
    NavigationItem("alerts", "Alerts", "Monitoring and streams", "live-intelligence", "live", 120),
    NavigationItem("scenarios", "Scenarios", "Compare and explore", "analytics-modeling", "analysis", 130),
    NavigationItem("research", "Research paths", "Investigations and briefs", "research-evidence", "research", 140),
    NavigationItem("integration", "API & embeds", "Institutional integration", "connectors-federation", "platform", 150),
    NavigationItem("experience", "Offline & access", "Mobile and performance", "standalone-application", "platform", 160),
    NavigationItem("earth", "Earth", "Satellite and orbital", "earth-environment", "science", 170),
    NavigationItem("spatial", "Spatial", "Areas and evidence", "analytics-modeling", "analysis", 180),
    NavigationItem("harmonization", "Harmonize", "Comparable series", "connectors-federation", "analysis", 190),
    NavigationItem("models", "Models", "Forecasts and warnings", "analytics-modeling", "analysis", 200),
    NavigationItem("evidence", "Evidence", "Claims and contradictions", "research-evidence", "research", 210),
    NavigationItem("graph", "Relationships", "Cross-domain graph", "research-evidence", "research", 220),
    NavigationItem("publishing", "Publishing", "Stories and maps", "research-evidence", "research", 230),
    NavigationItem("monitoring", "Monitoring", "Digests and feeds", "live-intelligence", "live", 240),
    NavigationItem("workspaces", "Workspaces", "Collaboration and review", "analytics-modeling", "research", 250),
    NavigationItem("workflows", "Workflows", "Cross-platform handoffs", "research-evidence", "research", 260),
    NavigationItem("federation", "Federation", "Standards and exchange", "connectors-federation", "platform", 270),
    NavigationItem("governance", "Governance", "Security and production", "law-governance", "platform", 280),
    NavigationItem("country", "Country", "Place-based evidence", "human-development", "intelligence", 290),
    NavigationItem("events", "Events", "Live event intelligence", "live-intelligence", "live", 300),
    NavigationItem("compare", "Compare", "Two-country context", "analytics-modeling", "analysis", 310),
    NavigationItem("thematic", "Themes", "Focused intelligence", "analytics-modeling", "analysis", 320),
    NavigationItem("briefing", "Briefing", "Briefs and exports", "research-evidence", "research", 330),
    NavigationItem("sources", "Sources", "Provenance and coverage", "connectors-federation", "research", 340),
    NavigationItem("saved", "Saved", "Local research paths", "standalone-application", "research", 350),
)


def runtime_mode(surface: str | None) -> str:
    value = (surface or "").strip().lower()
    if value in {"wordpress", "wordpress-embed", "embed"}:
        return "wordpress-embed"
    return "standalone-authoritative"


def session_contract() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "contract_version": SESSION_CONTRACT_VERSION,
        "authority": "browser-local",
        "authentication_required": False,
        "server_profile_required": False,
        "persistence": {
            "saved_views": "localStorage",
            "workspace_state": "URLSearchParams",
            "offline_shell": "CacheStorage",
            "server_mutation": False,
        },
        "portable_state": {
            "country": True,
            "view": True,
            "workspace_filters": True,
            "saved_view_exports": True,
        },
    }


def navigation_model(routes: Iterable[object]) -> dict:
    manifest = capability_manifest(routes)
    capability_ids = {item["capability_id"] for item in manifest["capabilities"]}
    items = []
    for item in sorted(NAVIGATION, key=lambda row: row.order):
        record = asdict(item)
        record["available"] = item.capability_id in capability_ids
        items.append(record)
    return {
        "ok": True,
        "version": APP_VERSION,
        "registry_version": manifest["registry_version"],
        "source": "/public/capabilities",
        "items": items,
        "groups": ["platform", "intelligence", "science", "live", "analysis", "research"],
    }


def build_bootstrap(routes: Iterable[object], surface: str | None = None) -> dict:
    manifest = capability_manifest(routes)
    mode = runtime_mode(surface)
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_name": RELEASE_NAME,
        "contract_version": STANDALONE_CONTRACT_VERSION,
        "authority": {
            "backend": "fastapi",
            "frontend": "standalone-web-app",
            "canonical_app_path": CANONICAL_APP_PATH,
            "canonical": True,
            "wordpress_role": "optional-integration-and-publication-surface",
        },
        "runtime": {
            "mode": mode,
            "api_base": "/",
            "app_base": CANONICAL_APP_PATH,
            "same_origin_api": True,
            "deep_links": True,
            "offline_shell": True,
        },
        "endpoints": {
            "health": "/health",
            "build_info": "/public/build-info",
            "capabilities": "/public/capabilities",
            "route_summary": "/public/routes/summary",
            "release_gate": "/public/release-gate",
            "runtime_handshake": "/public/app/runtime-handshake",
            "navigation": "/public/app/navigation",
            "session_contract": "/public/app/session-contract",
        },
        "assets": {
            "manifest": "/app/manifest.webmanifest",
            "service_worker": "/app/service-worker.js",
            "offline": "/app/offline.html",
            "cache_generation": CACHE_GENERATION,
            "asset_version": APP_VERSION,
        },
        "capability_registry": {
            "version": manifest["registry_version"],
            "capability_count": manifest["capability_count"],
            "route_count": manifest["route_count"],
            "modularized_route_count": manifest["modularized_route_count"],
            "unclassified_route_count": manifest["unclassified_route_count"],
        },
        "navigation": navigation_model(routes),
        "session": session_contract(),
    }


def runtime_handshake(routes: Iterable[object], client_version: str | None, surface: str | None = None) -> dict:
    supplied = (client_version or "").strip()
    compatible = supplied == APP_VERSION
    bootstrap = build_bootstrap(routes, surface)
    return {
        "ok": compatible,
        "version": APP_VERSION,
        "client_version": supplied or None,
        "compatible": compatible,
        "action": "continue" if compatible else "reload",
        "runtime_mode": bootstrap["runtime"]["mode"],
        "cache_generation": CACHE_GENERATION,
        "canonical_app_path": CANONICAL_APP_PATH,
        "bootstrap_endpoint": "/public/app/bootstrap",
    }
