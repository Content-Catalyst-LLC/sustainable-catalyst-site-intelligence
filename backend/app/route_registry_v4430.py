from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from fastapi.routing import APIRoute

from .version import APP_VERSION


@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    title: str
    domain: str
    description: str
    prefixes: tuple[str, ...]
    owner: str
    maturity: str = "production"


CAPABILITIES: tuple[CapabilitySpec, ...] = (
    CapabilitySpec("standalone-application", "Standalone Application Authority", "platform", "Canonical FastAPI-served Site Intelligence application, bootstrap, runtime handshake, navigation, session, offline shell, and deep-link contracts.", ("/public/app/", "/app"), "backend.app.routers.standalone"),
    CapabilitySpec("wordpress-integration", "WordPress Thin-Shell & Embed Bridge", "platform", "Compatibility bridge for WordPress navigation, embeds, release checks, optional auth handoff, and publication shell without product authority.", ("/public/integrations/wordpress",), "backend.app.routers.wordpress_bridge"),
    CapabilitySpec("system-runtime", "System Runtime", "platform", "Health, release identity, deployment, runtime recovery, and map interaction contracts.", ("/", "/health", "/public/build-info", "/public/deployment-", "/public/release-gate", "/public/runtime-", "/public/maps/", "/public/bootstrap-recovery", "/public/browser-reliability", "/public/embed-isolation", "/public/mutation-observer-recovery", "/public/performance-offline", "/public/startup-stability"), "backend.app.routers.system"),
    CapabilitySpec("capability-registry", "Capability Registry", "platform", "Machine-readable capability and route discovery for Site Intelligence.", ("/public/capabilities", "/public/routes/"), "backend.app.routers.capabilities"),
    CapabilitySpec("spatial-evidence-registry", "Unified Spatial Evidence & Layer Registry", "spatial", "Canonical cross-domain spatial evidence object, layer discovery, provenance, normalization, validation, and legacy spatial-studio compatibility contracts.", ("/public/spatial-evidence",), "backend.app.routers.spatial_evidence"),
    CapabilitySpec("spatiotemporal-analysis", "Spatiotemporal Query & Cross-Layer Analysis", "spatial", "Deterministic space-time filtering, cross-layer joins, aggregation, query planning, and provenance-preserving derived analysis over canonical spatial evidence objects.", ("/public/spatiotemporal",), "backend.app.routers.spatiotemporal"),
    CapabilitySpec("spatial-relationship-graph", "Spatial Relationship & Infrastructure Graph", "spatial", "Deterministic relationship graph over canonical spatial evidence with explicit infrastructure dependencies, connectivity, neighborhoods, paths, and provenance-preserving graph analysis.", ("/public/spatial-graph",), "backend.app.routers.spatial_graph"),
    CapabilitySpec("live-geospatial-fusion", "Live Geospatial Event Fusion", "live", "Canonical live-event normalization, strict cross-source reconciliation, freshness/lifecycle semantics, event-to-layer fusion, event-to-graph fusion, and provenance-preserving situational snapshots.", ("/public/live-geospatial",), "backend.app.routers.live_geospatial"),
    CapabilitySpec("global-source-federation", "Global Source Federation & Regional Authority Registry", "sources", "Global/regional source identity, jurisdiction scope, authority classification, deterministic source selection, federation planning, and user-trust separation over existing connector and precedence contracts.", ("/public/source-federation",), "backend.app.routers.source_federation"),
    CapabilitySpec("spatial-research-handoffs", "Spatial Research Object & Cross-Product Handoffs", "research", "Portable content-addressed spatial research objects, manifests, reproducible packages, and provider-neutral handoffs to Sustainable Catalyst products without implicit delivery or source mutation.", ("/public/spatial-research",), "backend.app.routers.spatial_research"),
    CapabilitySpec("data-truth", "Data Truth & Provenance", "evidence", "Country/source truth, control plane, record provenance, and workspace evidence.", ("/public/data-truth", "/public/record-truth", "/public/workspace-evidence", "/public/country-evidence", "/public/source-"), "backend.app.routers.data_truth"),
    CapabilitySpec("earth-environment", "Earth & Environmental Intelligence", "earth", "Earth observation, climate, atmosphere, cryosphere, hydrology, soils, ecosystems, biodiversity, and planetary boundaries.", ("/public/earth-observation", "/public/climate", "/public/atmosphere", "/public/cryosphere", "/public/hydrology", "/public/geosphere", "/public/soils-land", "/public/terrestrial-ecosystems", "/public/biodiversity", "/public/wetlands", "/public/planetary-boundaries", "/public/scientific-earth-systems", "/public/coastal-change", "/public/agriculture-food"), "backend.app.main"),
    CapabilitySpec("ocean-marine", "Ocean & Marine Intelligence", "ocean", "Ocean observation, missions, water column, seafloor, marine biodiversity, pollution, governance, and live underwater evidence.", ("/public/ocean", "/public/water-column", "/public/seafloor", "/public/underwater", "/public/marine-"), "backend.app.main"),
    CapabilitySpec("space-astronomy", "Space & Astronomy Intelligence", "space", "Orbital Earth, planetary, astronomical, SETI, exoplanet, solar-system, and live space observation.", ("/public/orbital-earth", "/public/planetary-intelligence", "/public/astronomical-observation", "/public/seti-technosignatures", "/public/exoplanet-habitability", "/public/solar-system-navigation", "/public/space-observation"), "backend.app.main"),
    CapabilitySpec("infrastructure-energy", "Infrastructure & Energy Intelligence", "infrastructure", "Energy systems, spatial energy, transportation, water, connectivity, industrial, mining, and built-environment intelligence.", ("/public/energy", "/v1/energy", "/public/transportation", "/public/water-sanitation", "/public/digital-connectivity", "/public/industrial-manufacturing", "/public/mining-critical-materials", "/public/human-settlements", "/public/solid-waste", "/public/trade-energy-resources"), "backend.app.main"),
    CapabilitySpec("human-development", "Human Development & Security", "human", "Humanitarian, conflict, food security, development, settlements, and country intelligence.", ("/public/human", "/public/food-security", "/public/country", "/public/countries", "/public/indicators", "/public/global-conditions", "/public/palestine-open-data"), "backend.app.main"),
    CapabilitySpec("law-governance", "Law & Governance", "governance", "International-law observatory, institutional governance, review, and production governance.", ("/public/international-law", "/public/institutional", "/public/production-governance"), "backend.app.main"),
    CapabilitySpec("live-intelligence", "Live Intelligence", "live", "Federated live-intelligence sources, events, alerts, feeds, digests, and monitoring.", ("/public/live-intelligence", "/public/events", "/public/alerts-monitoring", "/public/monitoring-operations", "/public/scheduled-monitoring", "/public/intelligence-digests", "/public/intelligence-feeds", "/public/early-warning"), "backend.app.main"),
    CapabilitySpec("research-evidence", "Research & Evidence Workflows", "research", "Research integration, evidence synthesis, knowledge graph, connected workflows, dossiers, and publications.", ("/public/research-", "/public/evidence-", "/public/knowledge-", "/public/connected-intelligence", "/public/intelligence-dossiers", "/public/publication-studio", "/public/intelligence-publications", "/public/source-aware-briefs", "/public/sustainable-development", "/public/economics-", "/public/history", "/public/briefing-studio", "/public/claims", "/public/intelligence-publishing", "/public/workflows", "/public/cross-platform-workflows", "/public/methodology", "/public/science-discovery"), "backend.app.main"),
    CapabilitySpec("analytics-modeling", "Analytics & Modeling", "analytics", "Assurance, scenarios, forecasts, comparisons, dashboards, model governance, and analytical workspaces.", ("/public/assurance", "/public/workspaces", "/public/compare", "/public/comparative-scenario", "/public/forecasts", "/public/forecast-evaluations", "/public/model-governance", "/public/models", "/public/dashboard", "/public/dashboards", "/public/thematic-dashboard", "/public/indicator-dashboards", "/public/spatial", "/public/geospatial", "/public/production-assurance", "/public/cross-domain-comparison"), "backend.app.main"),
    CapabilitySpec("connectors-federation", "Connectors & Federation", "sources", "Authoritative connectors, external-source resilience, harmonization, and data federation.", ("/public/authoritative-connectors", "/public/authoritative-apis", "/public/connectors", "/external", "/public/external-resilience", "/public/harmonization", "/public/public-data-api-integration", "/public/sources", "/public/credential-configuration"), "backend.app.main"),
    CapabilitySpec("platform-experience", "Platform & Experience", "experience", "Standalone app, navigation, launch, offline, publishing, SEO, reports, search, indexing, and administrative surfaces.", ("/app", "/public/v4", "/public/navigation", "/public/launch", "/public/experience-profile", "/public/offline-experience", "/publishing", "/reports", "/search", "/indexing", "/seo", "/admin", "/api", "/intelligence", "/analytics", "/registry", "/release", "/collect", "/ai", "/diagnostics", "/public/observatory", "/public/page-builder", "/public/saved-views", "/public/workspace-browser-audit", "/public/production-soak", "/public/page-templates", "/public/platform-core", "/public/landing-page", "/public/site-intelligence", "/public/status", "/public/topic-page-visual-qa", "/v1/public"), "backend.app.main"),
)


def classify_path(path: str) -> CapabilitySpec | None:
    # Longest matching prefix wins so specific families beat broad ones.
    matches: list[tuple[int, CapabilitySpec]] = []
    for spec in CAPABILITIES:
        for prefix in spec.prefixes:
            matched = path == prefix if prefix == "/" else (path == prefix or path.startswith(prefix))
            if matched:
                matches.append((len(prefix), spec))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def route_inventory(routes: Iterable[object]) -> list[dict]:
    items: list[dict] = []
    for route in routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        spec = classify_path(path)
        endpoint = route.endpoint
        source_module = getattr(endpoint, "__module__", "unknown")
        methods = sorted(method for method in (route.methods or set()) if method not in {"HEAD", "OPTIONS"})
        items.append(
            {
                "path": path,
                "methods": methods,
                "name": route.name,
                "operation_id": route.operation_id,
                "capability_id": spec.capability_id if spec else "legacy-unclassified",
                "source_module": source_module,
                "modularized": source_module.startswith("backend.app.routers") or source_module.startswith("app.routers"),
            }
        )
    items.sort(key=lambda item: (item["path"], item["methods"], item["name"]))
    return items


def capability_manifest(routes: Iterable[object]) -> dict:
    inventory = route_inventory(routes)
    specs = {spec.capability_id: spec for spec in CAPABILITIES}
    buckets: dict[str, list[dict]] = {key: [] for key in specs}
    buckets["legacy-unclassified"] = []
    for item in inventory:
        buckets.setdefault(item["capability_id"], []).append(item)

    capabilities = []
    for spec in CAPABILITIES:
        records = buckets.get(spec.capability_id, [])
        capabilities.append(
            {
                **asdict(spec),
                "route_count": len(records),
                "modularized_route_count": sum(1 for record in records if record["modularized"]),
                "methods": sorted({method for record in records for method in record["methods"]}),
            }
        )

    unclassified = buckets.get("legacy-unclassified", [])
    return {
        "ok": True,
        "version": APP_VERSION,
        "registry_version": "1.8.0",
        "capability_count": len(capabilities),
        "route_count": len(inventory),
        "modularized_route_count": sum(1 for item in inventory if item["modularized"]),
        "legacy_main_route_count": sum(1 for item in inventory if item["source_module"].endswith(".main")),
        "unclassified_route_count": len(unclassified),
        "capabilities": capabilities,
    }


def capability_detail(routes: Iterable[object], capability_id: str) -> dict | None:
    manifest = capability_manifest(routes)
    if capability_id == "legacy-unclassified":
        spec = {
            "capability_id": capability_id,
            "title": "Legacy Unclassified",
            "domain": "migration",
            "description": "Routes not yet mapped to a named v4.43 capability family.",
            "prefixes": [],
            "owner": "backend.app.main",
            "maturity": "migration",
        }
    else:
        match = next((spec for spec in CAPABILITIES if spec.capability_id == capability_id), None)
        if match is None:
            return None
        spec = asdict(match)
    records = [item for item in route_inventory(routes) if item["capability_id"] == capability_id]
    return {"ok": True, "version": APP_VERSION, **spec, "route_count": len(records), "routes": records}
