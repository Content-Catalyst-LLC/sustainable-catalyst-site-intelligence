from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .version import APP_VERSION


@dataclass(frozen=True)
class WorkspaceContract:
    route_id: str
    label: str
    scope: str
    completion: str
    controller: str | None
    surface_selectors: tuple[str, ...]
    endpoint_families: tuple[str, ...]
    empty_state: str
    degraded_state: str
    limitation: str
    lazy_load: bool = True


CORE = "operational"
BOUNDED = "operational-bounded"

ROUTES: tuple[WorkspaceContract, ...] = (
    WorkspaceContract("platform", "Connected platform", "public-discovery", BOUNDED, "SCConnectedPlatformV300", ("#connectedPlatform", "#routePanel"), ("/public/connected-platform",), "No approved public records match the current query.", "Connected search is temporarily limited; source distinctions remain visible.", "Public discovery only; private records and remote write operations are excluded."),
    WorkspaceContract("observatory", "Audit", "public-audit", BOUNDED, None, ("#auditablePublicObservatory", "#routePanel"), ("/public/observatory", "/public/build-info"), "No public audit records are registered for this view.", "Audit records are available, but one or more supporting diagnostics are unavailable.", "Integrity records support review but do not independently establish source authority."),
    WorkspaceContract("launch", "Launch", "public-portfolio", BOUNDED, None, ("#publicLaunchPortfolio", "#routePanel"), ("/public/release-status",), "No public launch materials are published.", "Release materials are partially available.", "Portfolio material describes product scope and is not a service-level guarantee."),
    WorkspaceContract("overview", "Overview", "live-cartography", CORE, None, ("#overviewLayout", "#map"), ("/public/geospatial/events", "/public/countries"), "The basemap is available, but no public event records match the current view.", "The map remains usable with local geography while one or more public feeds recover.", "Map proximity, density, and sequence do not establish causation or risk."),
    WorkspaceContract("global", "Global conditions", "global-observatory", CORE, "SCGlobalConditionsV210", ("#globalConditionsWorkspace", "#routePanel"), ("/public/global-conditions", "/public/geospatial/events"), "No current public conditions match the selected filters.", "Global conditions are partially available from marked cached or local records.", "Coverage varies by source, geography, and reporting cadence."),
    WorkspaceContract("economics", "Economics", "economic-observatory", CORE, "SCEconomicsV220", ("#economicsWorkspace", "#routePanel"), ("/public/economics",), "No comparable economic series match the current selection.", "Some economic providers are delayed; reporting periods and stale states remain visible.", "Economic series may differ in frequency, currency, price basis, and methodology."),
    WorkspaceContract("law", "International law", "law-observatory", CORE, "SCLawV230", ("#lawWorkspace", "#routePanel"), ("/public/international-law",), "No public legal records match the current selection.", "One or more legal repositories are unavailable; available authority and procedure fields remain visible.", "Legal records are research context, not legal advice or a determination of legal effect."),
    WorkspaceContract("science", "Science", "science-observatory", CORE, "SCScienceV240", ("#scienceWorkspace", "#routePanel"), ("/public/science",), "No scientific assets match the current filters.", "Some scientific or Earth-system services are unavailable; local catalog records remain visible.", "Scientific records retain source quality, uncertainty, and coverage limits."),
    WorkspaceContract("humanitarian", "Humanitarian", "humanitarian-observatory", CORE, "SCHumanitarianV250", ("#humanitarianWorkspace", "#routePanel"), ("/public/humanitarian",), "No public humanitarian records match the current view.", "Some humanitarian sources are delayed; cached records are visibly marked.", "This workspace is not an emergency service or an operational targeting system."),
    WorkspaceContract("resources", "Resources", "resource-observatory", CORE, "SCResourcesV260", ("#resourcesWorkspace", "#routePanel"), ("/public/resources",), "No trade, energy, food, water, or material records match the selection.", "Some resource datasets are delayed; units and periods remain explicit.", "Dependency and proximity do not establish vulnerability or causation."),
    WorkspaceContract("dossiers", "Dossiers", "country-regional-dossiers", CORE, "SCDossiersV270", ("#dossiersWorkspace", "#routePanel"), ("/public/dossiers",), "No published dossier matches the current geography.", "The dossier is partial because one or more evidence domains are unavailable.", "Dossiers do not collapse evidence into an automatic score or ranking."),
    WorkspaceContract("alerts", "Alerts", "browser-local-monitoring", CORE, "SCAlertsV280", ("#alertsWorkspace", "#routePanel"), ("/public/alerts",), "No public records currently match the browser-local alert rules.", "Live streams are reconnecting; no-match and source-failure states remain distinct.", "Alerts are informational and do not constitute official warnings."),
    WorkspaceContract("scenarios", "Scenarios", "comparative-scenarios", CORE, "SCScenariosV290", ("#scenariosWorkspace", "#routePanel"), ("/public/scenarios",), "No compatible series are selected for this scenario.", "Scenario inputs are partially available; incompatible fields remain blocked.", "Scenarios are transparent arithmetic explorations, not forecasts."),
    WorkspaceContract("research", "Research paths", "browser-local-research", BOUNDED, "SCResearchV2100", ("#researchWorkspace", "#routePanel"), ("/public/research-paths",), "No local research path has been created in this browser.", "Public evidence remains available, but one or more handoff targets are unavailable.", "Local research state is not a hosted account or proof of remote delivery."),
    WorkspaceContract("integration", "API & embeds", "public-integration", BOUNDED, "SCIntegrationV2110", ("#integrationWorkspace", "#routePanel"), ("/public/api", "/public/embed-manifest"), "No public integration contract matches the current filter.", "Some integration diagnostics are unavailable; read-only contracts remain visible.", "Public endpoints are read-only and do not imply institutional authentication."),
    WorkspaceContract("experience", "Offline & access", "delivery-contracts", BOUNDED, "SCExperienceV2120", ("#experienceWorkspace", "#routePanel"), ("/public/runtime-health", "/public/runtime-recovery"), "No cached workspace records are available in this browser.", "The shell is usable, but one or more optional offline or performance checks are unavailable.", "Offline data can become stale and is always labeled with its source state."),
    WorkspaceContract("earth", "Earth", "earth-observation", CORE, None, ("#earthStudio", "#earthMapA", "#earthMapB"), ("/public/earth-observation",), "No imagery is available for the selected layer and dates.", "Local geography remains visible while imagery services recover.", "Imagery coverage, cloud, latency, and processing limits remain explicit."),
    WorkspaceContract("spatial", "Spatial", "spatial-evidence", CORE, "SCSpatialV2150", ("#spatialEvidenceStudio", "#spatialEvidenceMap"), ("/public/spatial", "/public/spatial/areas"), "No registered public evidence intersects the selected area and layer.", "The map remains available while one or more spatial datasets recover.", "Spatial proximity and intersection do not establish causation or operational relevance."),
    WorkspaceContract("harmonization", "Harmonize", "comparable-series", CORE, "SCHarmonizationV2160", ("#harmonizationWorkspace", "#routePanel"), ("/public/harmonization",), "Select two public series to inspect comparability.", "One or more series are unavailable; no silent normalization is applied.", "The engine does not impute missing values or assume exchange rates."),
    WorkspaceContract("models", "Models", "model-governance", BOUNDED, "SCModelsV2170", ("#modelsWorkspace", "#routePanel"), ("/public/models",), "No published model or forecast records match the current view.", "Model records are partially available; evaluation gaps remain visible.", "Forecasts and thresholds are not guaranteed outcomes or emergency instructions."),
    WorkspaceContract("evidence", "Evidence", "claim-review", BOUNDED, "SCEvidenceV2180", ("#evidenceWorkspace", "#routePanel"), ("/public/claims",), "No approved claim is selected for review.", "Some evidence records are unavailable; contradictions and uncertainty remain visible.", "Deterministic synthesis cannot invent sources or conclusions."),
    WorkspaceContract("graph", "Relationships", "knowledge-graph", BOUNDED, "SCKnowledgeGraphV2190", ("#knowledgeGraphWorkspace", "#routePanel"), ("/public/knowledge-graph",), "No approved relationship records match the current entity.", "The graph is partially available; missing evidence links remain explicit.", "Graph paths, degree, and proximity do not establish causation or importance."),
    WorkspaceContract("publishing", "Publishing", "publications", BOUNDED, "SCIntelligencePublishingV2200", ("#publishingWorkspace", "#routePanel"), ("/public/publications",), "No human-approved publication is available for this selection.", "The directory is available, but one or more publication blocks could not load.", "Only human-approved public outputs are listed."),
    WorkspaceContract("monitoring", "Monitoring", "published-monitoring", BOUNDED, "SCScheduledMonitoringV2210", ("#monitoringWorkspace", "#routePanel"), ("/public/scheduled-monitoring",), "No human-approved digest or feed is currently published.", "Monitoring records are partially available; quiet periods and source failures remain distinguishable.", "Monitoring does not dispatch emergencies or take consequential action."),
    WorkspaceContract("workspaces", "Workspaces", "public-workspace-summaries", BOUNDED, "SCInstitutionalWorkspacesV2220", ("#institutionalWorkspaces", "#routePanel"), ("/public/institutional-workspaces",), "No institutional workspace has been explicitly published.", "Published summaries are partially available; private collaboration remains inaccessible.", "Membership, assignments, comments, and review notes are private."),
    WorkspaceContract("workflows", "Workflows", "workflow-registry", BOUNDED, "SCCrossPlatformWorkflowsV2230", ("#workflowWorkspace", "#routePanel"), ("/public/cross-platform-workflows",), "No public workflow route matches the current selection.", "The route registry is available, but a destination platform may be unavailable.", "Packet creation or export does not prove remote delivery."),
    WorkspaceContract("federation", "Federation", "public-federation", BOUNDED, "SCInstitutionalFederationV2240", ("#federationWorkspace", "#routePanel"), ("/public/federation",), "No public institutional catalog records match the current selection.", "Federated records are partially available; hosted, mirrored, and referenced states remain distinct.", "Remote catalogs are not fetched or imported automatically."),
    WorkspaceContract("governance", "Governance", "public-production-governance", BOUNDED, "SCProductionGovernanceV2250", ("#governanceWorkspace", "#routePanel"), ("/public/production-governance",), "No public production-governance records are available.", "Some operational diagnostics are unavailable; secrets and private records remain excluded.", "Public controls are evidence of implemented boundaries, not a compliance certification."),
    WorkspaceContract("country", "Country", "country-intelligence", CORE, None, ("#countryIntelligencePanel", "#countryOverviewMap"), ("/public/country-intelligence", "/public/country"), "No public country evidence is available for the selected geography.", "The country profile is partial; unavailable domains are visibly marked.", "Country evidence is not an automatic ranking, score, or policy determination."),
    WorkspaceContract("events", "Events", "event-intelligence", CORE, None, ("#eventStudio", "#eventExplorerMap"), ("/public/geospatial/events",), "No public events match the selected time, source, category, and geography filters.", "The event map remains usable while one or more feeds reconnect.", "Event absence does not prove that no real-world event occurred."),
    WorkspaceContract("compare", "Compare", "country-comparison", CORE, None, ("#compareStudio", "#compareMap"), ("/public/compare",), "Select two distinct countries with compatible public evidence.", "The comparison is partial; non-comparable fields remain blocked and labeled.", "Missing values and methodological differences are never silently normalized."),
    WorkspaceContract("thematic", "Themes", "thematic-intelligence", CORE, None, ("#thematicStudio", "#thematicMap"), ("/public/thematic",), "No public records match the selected theme and country.", "The thematic view is partial while one or more evidence families recover.", "Thematic groupings support exploration and do not establish causation or risk."),
    WorkspaceContract("briefing", "Briefing", "public-briefing", CORE, None, ("#briefingStudio", "#routePanel"), ("/public/briefing",), "Choose a supported briefing type and public subject.", "A source-aware partial briefing is available; unavailable sections are marked.", "Generated briefs organize public evidence and require human interpretation."),
    WorkspaceContract("sources", "Sources", "source-methodology", CORE, None, ("#sourceStudio", "#routePanel"), ("/public/sources",), "No public source record matches the current filters.", "Source diagnostics are partially available; last-success, last-attempt, and stale states remain distinct.", "A listed source is not automatically authoritative for every use."),
    WorkspaceContract("saved", "Saved", "browser-local-state", BOUNDED, None, ("#savedViewsStudio", "#routePanel"), (), "No view has been saved in this browser.", "Saved local state is available, but a referenced public route or source may be unavailable.", "Saved views are browser-local and do not prove remote storage or delivery."),
)

ROUTE_BY_ID = {route.route_id: route for route in ROUTES}


def _serialize(route: WorkspaceContract) -> dict[str, Any]:
    payload = asdict(route)
    payload["surface_selectors"] = list(route.surface_selectors)
    payload["endpoint_families"] = list(route.endpoint_families)
    payload["publicly_navigable"] = True
    payload["state_contract"] = ["initial", "ready", "empty", "degraded", "unavailable"]
    return payload


def public_production_truth() -> dict[str, Any]:
    routes = [_serialize(route) for route in ROUTES]
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_id": f"site-intelligence-v{APP_VERSION}",
        "contract": "production-truth-and-workspace-completion",
        "route_count": len(routes),
        "summary": {
            "operational": sum(route.completion == CORE for route in ROUTES),
            "operational_bounded": sum(route.completion == BOUNDED for route in ROUTES),
            "unavailable": 0,
            "lazy_loaded": sum(route.lazy_load for route in ROUTES),
        },
        "routes": routes,
        "policies": {
            "unfinished_routes": "A route without its required controller or surface is disabled and labeled unavailable.",
            "empty_data": "An empty result is distinct from a source failure and receives a route-specific empty state.",
            "degraded_data": "Available public records remain usable and stale or unavailable services are visibly marked.",
            "deep_links": "Supported routes restore from the view query parameter and browser history.",
            "request_scope": "Inactive workspaces do not open their controllers or initiate workspace-specific requests.",
            "recovery": "A recovered service refreshes only the active workspace.",
        },
    }


def public_production_truth_route(route_id: str) -> dict[str, Any] | None:
    route = ROUTE_BY_ID.get(route_id.strip().lower())
    if route is None:
        return None
    return {
        "ok": True,
        "version": APP_VERSION,
        "release_id": f"site-intelligence-v{APP_VERSION}",
        "route": _serialize(route),
    }
